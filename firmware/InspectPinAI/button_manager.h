#pragma once
#include <Arduino.h>
enum class ButtonAction { NONE, VOICE, CAMERA };
class ButtonManager {
 public: void begin(); ButtonAction update();
 private:
  struct Input {
    bool raw=true,stable=true,armed=false;
    uint32_t changed=0,pressed=0;
  } voice_,camera_;
  static void initialize(Input &input,int pin);
  static bool released(Input &input,int pin,uint32_t now);
};
