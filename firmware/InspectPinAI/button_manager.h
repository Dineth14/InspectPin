#pragma once
#include <Arduino.h>
enum class ButtonAction { NONE, VOICE, CAMERA };
class ButtonManager {
 public: void begin(); ButtonAction update();
 private: bool raw_=true,stable_=true; uint32_t changed_=0,pressed_=0;
};
