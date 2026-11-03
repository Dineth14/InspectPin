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
bool ButtonManager::released(Input &input,int pin,uint32_t now,uint32_t &heldMs) {
  bool raw=digitalRead(pin);
  if (raw!=input.raw) { input.raw=raw; input.changed=now; }
  if (now-input.changed>=40 && input.stable!=input.raw) {
    input.stable=input.raw;
    if (!input.stable) { input.pressed=now; input.armed=true; }
    else {
      bool event=input.armed;
      heldMs=now-input.pressed;
      input.armed=false;
      return event;
    }
  }
  return false;
}
ButtonAction ButtonManager::update() {
  uint32_t now=millis();
  uint32_t voiceHeld=0,secondHeld=0;
  bool voice=released(voice_,Config::button,now,voiceHeld);
  bool second=IP_CAMERA_BUTTON_ENABLED && released(camera_,Config::cameraButton,now,secondHeld);
  ButtonAction voiceAction=voice?ButtonPolicy::voiceRelease(voiceHeld,IP_BUTTON_LAYOUT_FINAL):ButtonAction::NONE;
  ButtonAction secondAction=second?ButtonPolicy::secondRelease(secondHeld,IP_BUTTON_LAYOUT_FINAL):ButtonAction::NONE;
  return ButtonPolicy::resolve(voiceAction,secondAction);
}
