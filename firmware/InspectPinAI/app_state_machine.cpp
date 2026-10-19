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
namespace { const char *names[]={"BOOT","INITIALIZING","READY","RECORDING","SAVING","UPLOADING","WAITING_FOR_AI","DOWNLOADING","PLAYING","OFFLINE","RETRYING","ERROR","LOW_BATTERY"}; }
void App::state(AppState value) { state_=value; Serial.printf("STATE %s\n",names[int(value)]); }
void App::fail(const String &error,bool offline) {
  Serial.printf("Error: %s. Captures retained on SD; 'r' retries pending work.\n",error.c_str());
  state(offline?AppState::OFFLINE:AppState::ERROR); Feedback::pulse();
}
bool App::idle() const { return state_==AppState::READY || state_==AppState::OFFLINE || state_==AppState::ERROR || state_==AppState::LOW_BATTERY; }
void App::begin() {
  state(AppState::INITIALIZING); Feedback::begin(); button_.begin(); Battery::begin();
  Serial.printf("PSRAM total=%u free=%u heap=%u\n",ESP.getPsramSize(),ESP.getFreePsram(),ESP.getFreeHeap());
  Serial.println("Commands: v=voice c=camera r=retry s=SD test w=Wi-Fi scan b=battery p=play /tone.wav");
  sdReady_=Store::begin();
  if (!sdReady_) { fail("SD_INITIALIZATION_FAILED"); return; }
  state(Wifi::connect()?AppState::READY:AppState::OFFLINE);
}
void App::capture(bool image) {
  if (!sdReady_) { fail("SD_NOT_READY"); return; }
  if (Battery::low()) { state(AppState::LOW_BATTERY); Serial.println("Battery low; recharge before recording"); return; }
  path_=Store::newPath(image); job_=""; attempts_=0;
  state(AppState::RECORDING); Feedback::pulse();
  bool ok=image?captureJpeg(path_):recordWav(path_);
  state(AppState::SAVING);
  if (!ok) { fail("CAPTURE_FAILED"); return; }
  if (!Store::markPending(path_)) { fail("PENDING_JOURNAL_FAILED"); return; }
  state(AppState::UPLOADING);
}
void App::retry() {
  if (!sdReady_) { begin(); return; }
  if (!Store::nextPending(path_,job_)) { Serial.println("No pending captures"); state(AppState::READY); return; }
  attempts_=0; jobStart_=millis(); lastPoll_=0;
  Serial.printf("Retrying saved input: %s\n",path_.c_str());
  state(job_.length()?AppState::WAITING_FOR_AI:AppState::UPLOADING);
}
void App::tick() {
  ButtonAction action=button_.update();
  if (idle()) {
    if (action==ButtonAction::VOICE) capture(false);
    else if (action==ButtonAction::CAMERA) capture(true);
    if (idle() && Serial.available()) {
      char cmd=Serial.read();
      if (cmd=='v') capture(false);
      else if (cmd=='c') capture(true);
      else if (cmd=='r') retry();
      else if (cmd=='s') Serial.println(Store::selfTest()?"SD test PASS":"SD test FAIL");
      else if (cmd=='w') { Wifi::scan(); Wifi::connect(); }
      else if (cmd=='b') Serial.printf("Battery voltage=%.3f V (disabled=-1)\n",Battery::volts());
      else if (cmd=='p') { state(AppState::PLAYING); if (playWav("/tone.wav")) state(AppState::READY); else fail("TONE_PLAYBACK_FAILED"); }
    }
    if (idle() && IP_BATTERY_ENABLED && millis()-lastBattery_>30000) {
      lastBattery_=millis();
      if (Battery::low()) { Serial.println("Battery low"); state(AppState::LOW_BATTERY); }
    }
  }
  String error; JobResult result_;
  if (state_==AppState::UPLOADING) {
    if (!Wifi::connect()) { fail("OFFLINE_RECORDING_SAVED",true); return; }
    if (!Api::upload(path_,job_,error)) {
      Serial.printf("Upload failed: %s\n",error.c_str());
      if (++attempts_<3) { retryAt_=millis(); state(AppState::RETRYING); }
      else fail(error,true);
      return;
    }
    Serial.printf("Job ID received: %s\n",job_.c_str());
    if (!Store::markPending(path_,job_)) { fail("JOB_JOURNAL_FAILED"); return; }
    jobStart_=millis(); lastPoll_=0; state(AppState::WAITING_FOR_AI);
  } else if (state_==AppState::RETRYING && millis()-retryAt_>=3000) state(AppState::UPLOADING);
  else if (state_==AppState::WAITING_FOR_AI) {
    if (millis()-jobStart_>Config::jobTimeoutMs) { fail("POLL_TIMEOUT",true); return; }
    if (millis()-lastPoll_<Config::pollIntervalMs) return;
    lastPoll_=millis();
    if (!Wifi::connect() || !Api::poll(job_,result_,error)) {
      if (error=="HTTP_404") { job_=""; Store::markPending(path_); }
      fail(error.length()?error:"WIFI_DISCONNECTED",true); return;
    }
    if (result_.status=="failed") { job_=""; Store::markPending(path_); fail(result_.error); return; }
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
