#pragma once
#include <Arduino.h>
#include <esp_timer.h>
#include "button_policy.h"
class ButtonManager {
 public:
  void begin();
  ButtonAction update();
  bool pressInProgress();
  void acceptDirectActions(bool enabled);
  void directPressCounts(uint32_t &ask, uint32_t &photo);
 private:
  struct Input {
    bool raw=true,stable=true,armed=false;
    uint32_t changed=0,pressed=0,presses=0;
  } voice_,camera_,pcfPhoto_;
  esp_timer_handle_t directTimer_=nullptr;
  portMUX_TYPE directLock_=portMUX_INITIALIZER_UNLOCKED;
  ButtonAction pending_=ButtonAction::NONE;
  bool accepting_=false;
  static void initialize(Input &input,int pin,int mode);
  static bool releasedLevel(Input &input,bool raw,uint32_t now,uint32_t &heldMs);
  static void sampleDirect(void *context);
  ButtonAction readDirect(uint32_t now);
};
