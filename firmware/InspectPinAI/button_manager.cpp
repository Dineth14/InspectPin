#include "button_manager.h"
#include "config.h"
#include "pcf8574_manager.h"
void ButtonManager::initialize(Input &input,int pin,int mode) {
  pinMode(pin,mode);
  input.raw=input.stable=digitalRead(pin);
  input.changed=input.pressed=millis();
  input.armed=false; // A button held at startup must not trigger on release.
}
void ButtonManager::begin() {
  if (directTimer_) return; // Already sampling after an SD initialization retry.
  if (Config::button>=0) initialize(voice_,Config::button,Config::buttonMode);
  else { voice_.raw=voice_.stable=true;voice_.changed=voice_.pressed=millis();voice_.armed=false; }
  if (IP_CAMERA_BUTTON_ENABLED) initialize(camera_,Config::cameraButton,INPUT_PULLUP);
  pcfPhoto_.raw=pcfPhoto_.stable=true;
  pcfPhoto_.changed=pcfPhoto_.pressed=millis();pcfPhoto_.armed=false;
  if (IP_PCF8574_ENABLED || (Config::button<0 && !IP_CAMERA_BUTTON_ENABLED)) return;
  esp_timer_create_args_t timerArgs{};
  timerArgs.callback=sampleDirect;
  timerArgs.arg=this;
  timerArgs.name="inspect-buttons";
  timerArgs.skip_unhandled_events=true;
  if (esp_timer_create(&timerArgs,&directTimer_)==ESP_OK) {
    if (esp_timer_start_periodic(directTimer_,5000)==ESP_OK) return;
    esp_timer_delete(directTimer_);
    directTimer_=nullptr;
  }
  Serial.println("Button sampler unavailable; using main-loop sampling");
}
bool ButtonManager::releasedLevel(Input &input,bool raw,uint32_t now,uint32_t &heldMs) {
  if (raw!=input.raw) { input.raw=raw; input.changed=now; }
  if (now-input.changed>=40 && input.stable!=input.raw) {
    input.stable=input.raw;
    if (!input.stable) { input.pressed=now; input.armed=true; ++input.presses; }
    else {
      bool event=input.armed;
      heldMs=now-input.pressed;
      input.armed=false;
      return event;
    }
  }
  return false;
}

ButtonAction ButtonManager::readDirect(uint32_t now) {
  uint32_t askHeld=0,photoHeld=0;
  const bool ask=Config::button>=0 &&
      releasedLevel(voice_,digitalRead(Config::button),now,askHeld);
  const bool photo=IP_CAMERA_BUTTON_ENABLED &&
      releasedLevel(camera_,digitalRead(Config::cameraButton),now,photoHeld);
  return ButtonPolicy::resolve(ask?ButtonPolicy::voiceRelease(askHeld):ButtonAction::NONE,
                              photo?ButtonPolicy::photoRelease(photoHeld):ButtonAction::NONE);
}

void ButtonManager::sampleDirect(void *context) {
  auto &manager=*static_cast<ButtonManager *>(context);
  portENTER_CRITICAL(&manager.directLock_);
  const ButtonAction action=manager.readDirect(millis());
  if (manager.accepting_ && manager.pending_==ButtonAction::NONE)
    manager.pending_=action;
  portEXIT_CRITICAL(&manager.directLock_);
}

ButtonAction ButtonManager::update() {
  if (directTimer_) {
    portENTER_CRITICAL(&directLock_);
    const ButtonAction action=pending_;
    pending_=ButtonAction::NONE;
    portEXIT_CRITICAL(&directLock_);
    return action;
  }
  const uint32_t now=millis();
  if (!IP_PCF8574_ENABLED) return readDirect(now);
  uint32_t askHeld=0,photoHeld=0;
  const bool ask=releasedLevel(voice_,!Expander::askPressed(),now,askHeld);
  const bool photo=releasedLevel(pcfPhoto_,!Expander::photoPressed(),now,photoHeld);
  return ButtonPolicy::resolve(ask?ButtonPolicy::voiceRelease(askHeld):ButtonAction::NONE,
                              photo?ButtonPolicy::photoRelease(photoHeld):ButtonAction::NONE);
}

void ButtonManager::acceptDirectActions(bool enabled) {
  portENTER_CRITICAL(&directLock_);
  accepting_=enabled;
  if (!enabled) pending_=ButtonAction::NONE;
  portEXIT_CRITICAL(&directLock_);
}

void ButtonManager::directPressCounts(uint32_t &ask, uint32_t &photo) {
  portENTER_CRITICAL(&directLock_);
  ask=voice_.presses;
  photo=camera_.presses;
  portEXIT_CRITICAL(&directLock_);
}

bool ButtonManager::pressInProgress() {
  const uint32_t now=millis();
  // A held or stuck input must not indefinitely suppress network service.
  const auto active=[now](const Input &input) {
    return input.raw!=input.stable || (input.armed && now-input.pressed<2500);
  };
  portENTER_CRITICAL(&directLock_);
  const bool pressed=active(voice_) || active(camera_) || active(pcfPhoto_);
  portEXIT_CRITICAL(&directLock_);
  return pressed;
}
