#include "app_state_machine.h"
#include "config.h"
#include "sd_manager.h"
#include "audio_recorder.h"
#include "audio_player.h"
#include "api_client.h"
#include "wifi_manager.h"
#include "camera_manager.h"
#include "battery_monitor.h"
#include "status_feedback.h"
#include "power_manager.h"
#include "command_dispatcher.h"
#include "event_log.h"
#include "settings_store.h"
#include "charge_status.h"
#include "illumination_controller.h"
#include "video_recorder.h"
#include "media_catalog.h"
#include "pcf8574_manager.h"
namespace { const char *names[]={"BOOT","INITIALIZING","READY","RECORDING","VIDEO_RECORDING","SAVING","UPLOADING","WAITING_FOR_AI","DOWNLOADING","PLAYING","OFFLINE","RETRYING","ERROR","LOW_BATTERY"}; }
void App::updateRuntimeState(AppState value) {
  TopLevelState top=TopLevelState::ACTIVE;
  ActiveState active=ActiveState::READY;
  switch(value) {
    case AppState::BOOT: top=TopLevelState::BOOTING; active=ActiveState::NONE; break;
    case AppState::INITIALIZING: top=TopLevelState::INITIALIZING; active=ActiveState::NONE; break;
    case AppState::RECORDING: active=path_.endsWith(".jpg")?ActiveState::IMAGE_CAPTURE:ActiveState::AUDIO_RECORDING; break;
    case AppState::VIDEO_RECORDING: active=ActiveState::VIDEO_RECORDING; break;
    case AppState::SAVING: active=ActiveState::MEDIA_SAVING; break;
    case AppState::UPLOADING: active=ActiveState::UPLOADING; break;
    case AppState::WAITING_FOR_AI: active=ActiveState::AI_PROCESSING; break;
    case AppState::DOWNLOADING: active=ActiveState::DOWNLOADING; break;
    case AppState::PLAYING: active=ActiveState::AUDIO_PLAYBACK; break;
    case AppState::RETRYING: top=TopLevelState::RECOVERY; active=ActiveState::NONE; break;
    case AppState::ERROR: top=TopLevelState::ERROR; active=ActiveState::NONE; break;
    default: break;
  }
  if (runtime_.current().top!=top && !runtime_.transitionTop(top)) {
    Serial.printf("STATE_TRANSITION_REJECTED from=%u to=%u\n",unsigned(runtime_.current().top),unsigned(top));
    EventLog::record(EventCode::OPERATION_FAILED,"invalid top-level transition");
    return;
  }
  if (top==TopLevelState::ACTIVE && !runtime_.transitionActive(active)) {
    Serial.printf("ACTIVE_TRANSITION_REJECTED to=%u\n",unsigned(active));
    EventLog::record(EventCode::OPERATION_FAILED,"invalid active transition");
    return;
  }
  runtime_.flags().connected=value!=AppState::OFFLINE;
  runtime_.flags().lowBattery=value==AppState::LOW_BATTERY;
}
void App::state(AppState value) {
  state_=value;
  switch(value) {
    case AppState::RECORDING: operation_.transition(OperationClass::CAPTURE); break;
    case AppState::VIDEO_RECORDING: operation_.transition(OperationClass::VIDEO); break;
    case AppState::SAVING: operation_.transition(OperationClass::MEDIA_WRITE); break;
    case AppState::UPLOADING: case AppState::DOWNLOADING: operation_.transition(OperationClass::NETWORK); break;
    case AppState::WAITING_FOR_AI: operation_.transition(OperationClass::AI_WAIT); break;
    case AppState::PLAYING: operation_.transition(OperationClass::PLAYBACK); break;
    case AppState::RETRYING: operation_.transition(OperationClass::RECOVERY); break;
    case AppState::READY: case AppState::OFFLINE: case AppState::ERROR: case AppState::LOW_BATTERY: operation_.end(); break;
    default: break;
  }
  updateRuntimeState(value);
  Serial.printf("STATE %s\n",names[int(value)]);
  EventLog::record(EventCode::STATE_TRANSITION,String("legacy=")+names[int(value)]+" top="+unsigned(runtime_.current().top)+" active="+unsigned(runtime_.current().active));
}
void App::fail(const String &error,bool offline) {
  Serial.printf("Error: %s. Captures retained on SD; 'r' retries pending work.\n",error.c_str());
  EventLog::record(EventCode::OPERATION_FAILED,error);
  operation_.end(); state(offline?AppState::OFFLINE:AppState::ERROR); Feedback::signal(Feedback::Event::ERROR);
}
bool App::idle() const { return state_==AppState::READY || state_==AppState::OFFLINE || state_==AppState::ERROR || state_==AppState::LOW_BATTERY; }
void App::begin() {
  EventLog::begin();
  state(AppState::INITIALIZING); Expander::begin(); Feedback::begin(); Illumination::begin(); button_.begin(); Battery::begin(); ChargeStatus::begin(); Power::begin();
  if(!SettingsStore::begin()) Serial.println("Settings store unavailable; compile-time defaults active");
  Power::setIdleTimeout(SettingsStore::get().idleTimeoutMs);
  Serial.printf("PSRAM total=%u free=%u heap=%u\n",ESP.getPsramSize(),ESP.getFreePsram(),ESP.getFreeHeap());
  Serial.printf("Device ID: %s\n",Api::deviceId().c_str());
  Serial.println("Commands: v=voice c=photo u=video-start o=video-stop m=media k=camera i=context x=clear r=retry s=SD w=Wi-Fi b=battery p=tone z=sleep d=buttons");
  Serial.println(IP_CAMERA_BUTTON_ENABLED ? "Buttons: D2/GPIO3=voice, D5/GPIO6=camera (press and release)" : "Button D2/GPIO3: short=voice, long=camera");
  sdReady_=Store::begin();
  if (!sdReady_) { fail("SD_INITIALIZATION_FAILED"); return; }
  Video::recoverIncomplete();
  Video::recoverIncomplete();
  if (Wifi::connect()) syncContext();
  else state(AppState::OFFLINE);
}
void App::useContext(const SessionContext &context) {
  context_=context; contextAt_=millis();
  Serial.printf("Context=%s active image=%s remaining=%lu seconds\n",context_.contextId.c_str(),
                context_.imageId.length()?context_.imageId.c_str():"none",(unsigned long)(context_.remainingMs/1000));
}
void App::syncContext(bool clear) {
  SessionContext current; String error;
  if (!Wifi::connect() || !Api::session(current,error,clear)) {
    fail(error.length()?error:"SERVER_UNAVAILABLE",true); return;
  }
  useContext(current);
  if (clear) { imagePending_=false; Serial.println("Conversation and image context cleared; voice-only mode"); }
  state(AppState::READY);
}
void App::capture(bool image) {
  if (!operation_.begin(OperationClass::CAPTURE)) { fail("DEVICE_BUSY"); return; }
  if (!sdReady_) { fail("SD_NOT_READY"); return; }
  if (Battery::low()) { state(AppState::LOW_BATTERY); Serial.println("Battery low; recharge before recording"); return; }
  if (!image && imagePending_) { fail("IMAGE_UPLOAD_PENDING: send r before asking about this photo"); return; }
  if (!image && context_.imageId.length() && millis()-contextAt_>=context_.remainingMs) {
    fail("IMAGE_EXPIRED: capture again with c or clear with x"); return;
  }
  captureImage_=image?"":context_.imageId;
  captureContext_=image?"":context_.contextId;
  path_=Store::newPath(image); job_=""; jobResult_=JobResult{}; attempts_=0;
  state(AppState::RECORDING); Feedback::signal(Feedback::Event::RECORDING_STARTED); Power::noteActivity();
  if(image) Illumination::photoBegin(Battery::latest().low);
  bool ok=image?captureJpeg(path_):recordWav(path_);
  if(image) Illumination::photoEnd();
  state(AppState::SAVING);
  if (!ok) { fail("CAPTURE_FAILED"); return; }
  if (image) imagePending_=true;
  if (!Store::markPending(path_,"",captureImage_,captureContext_)) { fail("PENDING_JOURNAL_FAILED"); return; }
  state(AppState::UPLOADING);
}
void App::retry() {
  if (!operation_.begin(OperationClass::RECOVERY)) { fail("DEVICE_BUSY"); return; }
  if (!sdReady_) { begin(); return; }
  if (!Store::nextPending(path_,job_,captureImage_,captureContext_)) { Serial.println("No pending captures"); state(AppState::READY); return; }
  jobResult_=JobResult{};
  if (path_.endsWith(".jpg")) { job_=""; imagePending_=true; }
  attempts_=0; jobStart_=millis(); lastPoll_=0;
  Serial.printf("Retrying saved input: %s\n",path_.c_str());
  state(job_.length()?AppState::WAITING_FOR_AI:AppState::UPLOADING);
}
void App::handleCommand(const DeviceCommand &command) {
  DispatchDecision decision=CommandDispatcher::validate(command,runtime_.current(),operation_);
  if(!decision.accepted) {
    if(command.type!=CommandType::NONE) {
      Serial.printf("COMMAND_REJECTED request=%s error=%s actual=%s\n",command.requestId.c_str(),decision.errorCode,names[int(state_)]);
      EventLog::record(EventCode::COMMAND_REJECTED,String(Commands::name(command.type))+" "+decision.errorCode);
    }
    return;
  }
  Power::noteActivity(); Serial.printf("COMMAND %s source=%u request=%s\n",Commands::name(command.type),unsigned(command.source),command.requestId.c_str());
  EventLog::record(EventCode::COMMAND_ACCEPTED,String(Commands::name(command.type))+" "+command.requestId);
  switch(command.type) {
    case CommandType::VOICE_START: capture(false); break;
    case CommandType::PHOTO_CAPTURE: capture(true); break;
    case CommandType::VIDEO_START:
      if(!operation_.begin(OperationClass::VIDEO)){fail("DEVICE_BUSY");break;}
      path_=Store::newVideoPath();
      if(Video::begin(path_)){state(AppState::VIDEO_RECORDING);Feedback::signal(Feedback::Event::VIDEO_STARTED);}
      else {Serial.printf("Video start failed: %s\n",Video::stats().error.c_str());fail(Video::stats().error);}
      break;
    case CommandType::VIDEO_STOP:
      if(Video::stop("command")){Feedback::signal(Feedback::Event::VIDEO_STOPPED);state(AppState::READY);}else fail("VIDEO_STOP_FAILED");
      break;
    case CommandType::RETRY: retry(); break;
    case CommandType::CONTEXT_GET: syncContext(); break;
    case CommandType::CONTEXT_CLEAR: syncContext(true); break;
    case CommandType::SD_TEST: Serial.println(Store::selfTest()?"SD test PASS":"SD test FAIL"); break;
    case CommandType::MEDIA_LIST: MediaCatalog::print(); break;
    case CommandType::MEDIA_DOWNLOAD: MediaCatalog::sendFile(Video::stats().path); break;
    case CommandType::WIFI_CONNECT: Wifi::scan(); Wifi::connect(); break;
    case CommandType::BATTERY_GET: { auto reading=Battery::sample(); auto charge=ChargeStatus::latest(); Serial.printf("Battery voltage=%.3f V estimate=%.1f%% valid=%s uncertainty=%.2f V low=%s critical=%s calibration=%.4f charge=%s charge_valid=%s source=%s age_ms=%lu\n",reading.volts,reading.percent,reading.valid?"yes":"no",reading.uncertaintyVolts,reading.low?"yes":"no",reading.critical?"yes":"no",Battery::calibration(),ChargeStatus::name(charge.state),charge.valid?"yes":"no",charge.source,(unsigned long)charge.ageMs); break; }
    case CommandType::CAMERA_DIAGNOSTIC: Serial.println(diagnoseCamera()?"Camera profile diagnostic PASS":"Camera profile diagnostic FAIL"); break;
    case CommandType::TONE_PLAY: state(AppState::PLAYING); if(playWav("/tone.wav")) state(AppState::READY); else fail("TONE_PLAYBACK_FAILED"); break;
    case CommandType::LIGHT_SET: {
      Illumination::Error lightError;
      if(!Illumination::set(command.boolValue,command.intValue,IP_LIGHT_TIMEOUT_MS,Battery::latest().low,lightError))
        Serial.printf("COMMAND_FAILED request=%s error=%s actual_light=%s\n",command.requestId.c_str(),Illumination::errorName(lightError),Illumination::state().actual?"on":"off");
      else Serial.printf("COMMAND_COMPLETED request=%s actual_light=%s brightness=%u\n",command.requestId.c_str(),Illumination::state().actual?"on":"off",Illumination::state().brightness);
      break;
    }
    case CommandType::VOLUME_SET: {
      if(command.intValue<0||command.intValue>100) { Serial.printf("COMMAND_FAILED request=%s error=INVALID_VOLUME\n",command.requestId.c_str()); break; }
      setPlaybackVolume(uint8_t(command.intValue));
      DeviceSettings settings=SettingsStore::get();settings.volumePercent=playbackVolume();SettingsStore::update(settings);
      Serial.printf("COMMAND_COMPLETED request=%s volume=%u\n",command.requestId.c_str(),playbackVolume());break;
    }
    case CommandType::HAPTIC_SET: {
      if(command.intValue<0||command.intValue>255){Serial.printf("COMMAND_FAILED request=%s error=INVALID_HAPTIC_INTENSITY\n",command.requestId.c_str());break;}
      Feedback::setHaptic(command.boolValue,uint8_t(command.intValue));
      Serial.printf("COMMAND_COMPLETED request=%s haptic=%s intensity=%u\n",command.requestId.c_str(),Feedback::hapticEnabled()?"on":"off",Feedback::hapticIntensity());break;
    }
    case CommandType::RESTART: Serial.printf("COMMAND_COMPLETED request=%s actual=RESTARTING\n",command.requestId.c_str());Serial.flush();ESP.restart();break;
    case CommandType::SLEEP:
      if(!operation_.sleepSafe()) { Serial.println("Sleep deferred: operation active"); EventLog::record(EventCode::SLEEP_DEFERRED,command.requestId); }
      else {
        SettingsStore::end(); Store::end();
        if(!Power::enterAutomaticSleep("manual/idle command")) {
          Serial.printf("COMMAND_FAILED request=%s error=POWER_FEATURE_DISABLED actual=%s\n",command.requestId.c_str(),names[int(state_)]);
          EventLog::record(EventCode::OPERATION_FAILED,"POWER_FEATURE_DISABLED");
        }
        sdReady_=Store::begin(); SettingsStore::begin();Power::setIdleTimeout(SettingsStore::get().idleTimeoutMs);
      }
      break;
    case CommandType::STATUS_GET: {auto video=Video::stats();Serial.printf("STATE %s heap=%u psram=%u connected=%s light=%s brightness=%u haptic=%s volume=%u video=%s frames=%lu dropped=%lu bytes=%lu\n",names[int(state_)],ESP.getFreeHeap(),ESP.getFreePsram(),runtime_.current().flags.connected?"yes":"no",Illumination::state().actual?"on":"off",Illumination::state().brightness,Feedback::hapticEnabled()?"on":"off",playbackVolume(),video.active?"recording":"idle",(unsigned long)video.frames,(unsigned long)video.dropped,(unsigned long)video.bytes);break;}
    default: Serial.printf("Command unsupported in current phase: %s\n",Commands::name(command.type)); break;
  }
}
void App::tick() {
  Feedback::tick();
  Expander::tick();
  ChargeStatus::tick();
  Illumination::tick(Battery::latest().low);
  runtime_.flags().lightOn=Illumination::state().actual;
  runtime_.flags().hapticEnabled=Feedback::hapticEnabled();
  ButtonAction action=button_.update();
  if(Video::active()) {
    if(IP_BATTERY_ENABLED&&millis()-lastBattery_>1000){lastBattery_=millis();Battery::sample();}
    Video::tick(Battery::latest().critical);
    if(action!=ButtonAction::NONE&&Video::active()) handleCommand({CommandType::VIDEO_STOP,CommandSource::BUTTON,String("button-")+millis()});
    if(Serial.available()&&Video::active()) handleCommand(Commands::fromSerial(Serial.read()));
    if(!Video::active()&&state_==AppState::VIDEO_RECORDING){operation_.end();state(AppState::READY);}
    return;
  }
  if (idle()) {
    if (action==ButtonAction::VOICE) handleCommand({CommandType::VOICE_START,CommandSource::BUTTON,String("button-")+millis()});
    else if (action==ButtonAction::CAMERA) handleCommand({CommandType::PHOTO_CAPTURE,CommandSource::BUTTON,String("button-")+millis()});
    if (idle() && Serial.available()) {
      char cmd=Serial.read();
      if(cmd=='d') Serial.printf("Buttons: D2/GPIO3=%s D5/GPIO6=%s two-button=%s (pressed=LOW)\n",
        digitalRead(Config::button)?"HIGH":"LOW",digitalRead(Config::cameraButton)?"HIGH":"LOW",IP_CAMERA_BUTTON_ENABLED?"yes":"no");
      else handleCommand(Commands::fromSerial(cmd));
    }
    if (idle() && IP_BATTERY_ENABLED && millis()-lastBattery_>30000) {
      lastBattery_=millis();
      if (Battery::low()) { Serial.println("Battery low"); state(AppState::LOW_BATTERY); }
    }
  }
  if(idle()&&operation_.sleepSafe()&&Power::idleExpired()) handleCommand({CommandType::SLEEP,CommandSource::INTERNAL,"idle-timeout"});
  String error;
  if (state_==AppState::UPLOADING) {
    if (!Wifi::connect()) { fail("OFFLINE_RECORDING_SAVED",true); return; }
    if (path_.endsWith(".jpg")) {
      SessionContext current;
      if (!Api::uploadImage(path_,current,error)) {
        Serial.printf("Image upload failed: %s\n",error.c_str());
        if (++attempts_<3) { retryAt_=millis(); state(AppState::RETRYING); } else fail(error,true);
        return;
      }
      useContext(current); imagePending_=false; Store::complete(path_);
      Serial.println("Image registered. Short press or send v, then ask a question about this image.");
      Feedback::pulse(); state(AppState::READY); return;
    }
    String returnedContext;
    if (!Api::upload(path_,job_,error,captureImage_,captureContext_,&returnedContext)) {
      Serial.printf("Upload failed: %s\n",error.c_str());
      if (error=="IMAGE_EXPIRED" || error=="CONTEXT_CHANGED" || error=="IMAGE_NOT_FOUND" || error=="IMAGE_ID_REQUIRED") {
        fail(error+": use i to inspect context, c to recapture, or x to clear. Original WAV pairing retained.");
      } else if (++attempts_<3) { retryAt_=millis(); state(AppState::RETRYING); }
      else fail(error,true);
      return;
    }
    Serial.printf("Job ID received: %s\n",job_.c_str());
    if (!captureContext_.length()) {
      captureContext_=returnedContext;
      if (captureImage_==context_.imageId) context_.contextId=returnedContext;
    }
    if (!Store::markPending(path_,job_,captureImage_,captureContext_)) { fail("JOB_JOURNAL_FAILED"); return; }
    jobStart_=millis(); lastPoll_=0; state(AppState::WAITING_FOR_AI);
  } else if (state_==AppState::RETRYING && millis()-retryAt_>=3000) state(AppState::UPLOADING);
  else if (state_==AppState::WAITING_FOR_AI) {
    if (millis()-jobStart_>Config::jobTimeoutMs) { fail("POLL_TIMEOUT",true); return; }
    if (millis()-lastPoll_<Config::pollIntervalMs) return;
    lastPoll_=millis();
    if (!Wifi::connect() || !Api::poll(job_,jobResult_,error)) {
      if (error=="HTTP_404" || error=="JOB_NOT_FOUND") { job_=""; Store::markPending(path_,"",captureImage_,captureContext_); }
      fail(error.length()?error:"WIFI_DISCONNECTED",true); return;
    }
    if (jobResult_.status=="failed") { job_=""; Store::markPending(path_,"",captureImage_,captureContext_); fail(jobResult_.error); return; }
    if (jobResult_.status=="completed" && jobResult_.audio) {
      Serial.printf("Speech recognized: %s\nAI processing completed: %s\n",jobResult_.transcript.c_str(),jobResult_.answer.c_str());
      answerPath_=String("/inspectpin/answer_")+job_+".wav"; state(AppState::DOWNLOADING);
    }
  } else if (state_==AppState::DOWNLOADING) {
    if (!Api::download(job_,answerPath_,error)) { fail(error,true); return; }
    state(AppState::PLAYING);
  } else if (state_==AppState::PLAYING) {
    if (!playWav(answerPath_)) { fail("PLAYBACK_FAILED"); return; }
    Store::complete(path_); Feedback::pulse(); state(AppState::READY);
    if(jobResult_.hasCommand) { DeviceCommand command=jobResult_.command; jobResult_.hasCommand=false; handleCommand(command); }
    if (IP_DEBUG) Serial.printf("Free heap=%u PSRAM=%u\n",ESP.getFreeHeap(),ESP.getFreePsram());
  }
}
