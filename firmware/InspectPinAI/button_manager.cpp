#include "button_manager.h"
#include "config.h"
void ButtonManager::initialize(Input &input,int pin) {
  pinMode(pin,INPUT_PULLUP);
  input.raw=input.stable=digitalRead(pin);
  input.changed=input.pressed=millis();
  input.armed=false; // A button held at startup must not trigger on release.
}
void ButtonManager::begin() {
  initialize(voice_,Config::button);
  if (IP_CAMERA_BUTTON_ENABLED) initialize(camera_,Config::cameraButton);
}
bool ButtonManager::released(Input &input,int pin,uint32_t now) {
  bool raw=digitalRead(pin);
  if (raw!=input.raw) { input.raw=raw; input.changed=now; }
  if (now-input.changed>=40 && input.stable!=input.raw) {
    input.stable=input.raw;
    if (!input.stable) { input.pressed=now; input.armed=true; }
    else {
      bool event=input.armed;
      input.armed=false;
      return event;
    }
  }
  return false;
}
ButtonAction ButtonManager::update() {
  uint32_t now=millis();
  bool voice=released(voice_,Config::button,now);
  bool camera=IP_CAMERA_BUTTON_ENABLED && released(camera_,Config::cameraButton,now);
  // Sample both inputs every tick; simultaneous release causes only one action.
  if (camera) return ButtonAction::CAMERA;
  if (voice) return !IP_CAMERA_BUTTON_ENABLED && now-voice_.pressed>=1200
                      ?ButtonAction::CAMERA:ButtonAction::VOICE;
  return ButtonAction::NONE;
}
