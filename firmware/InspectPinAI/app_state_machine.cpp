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
namespace { const char *names[]={"BOOT","INITIALIZING","READY","RECORDING","SAVING","UPLOADING","WAITING_FOR_AI","DOWNLOADING","PLAYING","OFFLINE","RETRYING","ERROR","LOW_BATTERY"}; }
void App::state(AppState value) {
  state_=value;
  switch(value) {
    case AppState::RECORDING: operation_.transition(OperationClass::CAPTURE); break;
    case AppState::SAVING: operation_.transition(OperationClass::MEDIA_WRITE); break;
    case AppState::UPLOADING: case AppState::DOWNLOADING: operation_.transition(OperationClass::NETWORK); break;
    case AppState::WAITING_FOR_AI: operation_.transition(OperationClass::AI_WAIT); break;
    case AppState::PLAYING: operation_.transition(OperationClass::PLAYBACK); break;
    case AppState::RETRYING: operation_.transition(OperationClass::RECOVERY); break;
    case AppState::READY: case AppState::OFFLINE: case AppState::ERROR: case AppState::LOW_BATTERY: operation_.end(); break;
    default: break;
  }
  Serial.printf("STATE %s\n",names[int(value)]);
}
void App::fail(const String &error,bool offline) {
  Serial.printf("Error: %s. Captures retained on SD; 'r' retries pending work.\n",error.c_str());
  operation_.end(); state(offline?AppState::OFFLINE:AppState::ERROR); Feedback::signal(Feedback::Event::ERROR);
}
bool App::idle() const { return state_==AppState::READY || state_==AppState::OFFLINE || state_==AppState::ERROR || state_==AppState::LOW_BATTERY; }
void App::begin() {
  state(AppState::INITIALIZING); Feedback::begin(); button_.begin(); Battery::begin(); Power::begin();
  Serial.printf("PSRAM total=%u free=%u heap=%u\n",ESP.getPsramSize(),ESP.getFreePsram(),ESP.getFreeHeap());
  Serial.printf("Device ID: %s\n",Api::deviceId().c_str());
  Serial.println("Commands: v=voice c=photo k=camera i=context x=clear r=retry s=SD w=Wi-Fi b=battery p=tone z=sleep d=buttons");
  Serial.println(IP_CAMERA_BUTTON_ENABLED ? "Buttons: D2/GPIO3=voice, D5/GPIO6=camera (press and release)" : "Button D2/GPIO3: short=voice, long=camera");
  sdReady_=Store::begin();
  if (!sdReady_) { fail("SD_INITIALIZATION_FAILED"); return; }
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
  path_=Store::newPath(image); job_=""; attempts_=0;
  state(AppState::RECORDING); Feedback::signal(Feedback::Event::RECORDING_STARTED); Power::noteActivity();
  bool ok=image?captureJpeg(path_):recordWav(path_);
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
  if (path_.endsWith(".jpg")) { job_=""; imagePending_=true; }
  attempts_=0; jobStart_=millis(); lastPoll_=0;
  Serial.printf("Retrying saved input: %s\n",path_.c_str());
  state(job_.length()?AppState::WAITING_FOR_AI:AppState::UPLOADING);
}
void App::handleCommand(const DeviceCommand &command) {
  if(command.type==CommandType::NONE) return;
  Power::noteActivity(); Serial.printf("COMMAND %s source=%u request=%s\n",Commands::name(command.type),unsigned(command.source),command.requestId.c_str());
  switch(command.type) {
    case CommandType::VOICE_START: capture(false); break;
    case CommandType::PHOTO_CAPTURE: capture(true); break;
    case CommandType::RETRY: retry(); break;
    case CommandType::CONTEXT_GET: syncContext(); break;
    case CommandType::CONTEXT_CLEAR: syncContext(true); break;
    case CommandType::SD_TEST: Serial.println(Store::selfTest()?"SD test PASS":"SD test FAIL"); break;
    case CommandType::WIFI_CONNECT: Wifi::scan(); Wifi::connect(); break;
    case CommandType::BATTERY_GET: { auto reading=Battery::sample(); Serial.printf("Battery voltage=%.3f V estimate=%.1f%% valid=%s uncertainty=%.2f V\n",reading.volts,reading.percent,reading.valid?"yes":"no",reading.uncertaintyVolts); break; }
    case CommandType::CAMERA_DIAGNOSTIC: Serial.println(diagnoseCamera()?"Camera profile diagnostic PASS":"Camera profile diagnostic FAIL"); break;
    case CommandType::TONE_PLAY: state(AppState::PLAYING); if(playWav("/tone.wav")) state(AppState::READY); else fail("TONE_PLAYBACK_FAILED"); break;
    case CommandType::SLEEP:
      if(!operation_.sleepSafe()) Serial.println("Sleep deferred: operation active");
      else { Store::end(); Power::enterDeepSleep("manual command"); sdReady_=Store::begin(); }
      break;
    case CommandType::STATUS_GET: Serial.printf("STATE %s heap=%u psram=%u\n",names[int(state_)],ESP.getFreeHeap(),ESP.getFreePsram()); break;
    default: Serial.printf("Command unsupported in current phase: %s\n",Commands::name(command.type)); break;
  }
}
void App::tick() {
  Feedback::tick();
  ButtonAction action=button_.update();
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
  String error; JobResult result_;
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
    if (!Wifi::connect() || !Api::poll(job_,result_,error)) {
      if (error=="HTTP_404" || error=="JOB_NOT_FOUND") { job_=""; Store::markPending(path_,"",captureImage_,captureContext_); }
      fail(error.length()?error:"WIFI_DISCONNECTED",true); return;
    }
    if (result_.status=="failed") { job_=""; Store::markPending(path_,"",captureImage_,captureContext_); fail(result_.error); return; }
    if (result_.status=="completed" && result_.audio) {
      Serial.printf("Speech recognized: %s\nAI processing completed: %s\n",result_.transcript.c_str(),result_.answer.c_str());
      answerPath_=String("/inspectpin/answer_")+job_+".wav"; state(AppState::DOWNLOADING);
    }
  } else if (state_==AppState::DOWNLOADING) {
    if (!Api::download(job_,answerPath_,error)) { fail(error,true); return; }
    state(AppState::PLAYING);
  } else if (state_==AppState::PLAYING) {
    if (!playWav(answerPath_)) { fail("PLAYBACK_FAILED"); return; }
    Store::complete(path_); Feedback::pulse(); state(AppState::READY);
    if (IP_DEBUG) Serial.printf("Free heap=%u PSRAM=%u\n",ESP.getFreeHeap(),ESP.getFreePsram());
  }
}
