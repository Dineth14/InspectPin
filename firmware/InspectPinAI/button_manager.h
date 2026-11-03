#pragma once
#include <Arduino.h>
#include "button_policy.h"
class ButtonManager {
 public: void begin(); ButtonAction update();
 private:
  struct Input {
    bool raw=true,stable=true,armed=false;
    uint32_t changed=0,pressed=0;
  } voice_,camera_,pcfPhoto_;
  static void initialize(Input &input,int pin);
  static bool released(Input &input,int pin,uint32_t now,uint32_t &heldMs);
  static bool releasedLevel(Input &input,bool raw,uint32_t now,uint32_t &heldMs);
};
