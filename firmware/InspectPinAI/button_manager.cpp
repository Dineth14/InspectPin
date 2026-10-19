#include "button_manager.h"
#include "config.h"
void ButtonManager::begin() { pinMode(Config::button,INPUT_PULLUP); raw_=stable_=digitalRead(Config::button); pressed_=millis(); }
ButtonAction ButtonManager::update() {
  bool raw=digitalRead(Config::button); uint32_t now=millis();
  if (raw!=raw_) { raw_=raw; changed_=now; }
  if (now-changed_>=40 && stable_!=raw_) {
    stable_=raw_;
    if (!stable_) pressed_=now;
    else return now-pressed_>=1200?ButtonAction::CAMERA:ButtonAction::VOICE;
  }
  return ButtonAction::NONE;
}
