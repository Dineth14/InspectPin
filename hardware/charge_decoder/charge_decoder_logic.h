#pragma once
#include <stdint.h>

namespace ChargeDecoder {
enum class State : uint8_t { USB_ABSENT, STARTUP, CHARGING, FULL };
struct Output { State state; bool ledOn; };

class Controller {
 public:
  Output update(bool vbus,bool nChgLow,uint32_t nowMs) {
    if(!vbus){reset(nowMs);state_=State::USB_ABSENT;return {state_,false};}
    if(state_==State::USB_ABSENT){reset(nowMs);state_=State::STARTUP;}
    if(nChgLow){
      if(!low_){low_=true;lowSince_=nowMs;}
      if(nowMs-lowSince_>=fullThresholdMs){state_=State::FULL;fullLatched_=true;}
    } else if(low_) {
      const uint32_t width=nowMs-lowSince_;
      low_=false;
      if(width>=pulseMinMs&&width<=pulseMaxMs&&!fullLatched_) state_=State::CHARGING;
    }
    if(fullLatched_) state_=State::FULL;
    const bool led=state_==State::FULL ||
      (state_==State::CHARGING && ((nowMs/500U)&1U)==0U);
    return {state_,led};
  }
 private:
  static constexpr uint32_t pulseMinMs=80;
  static constexpr uint32_t pulseMaxMs=300;
  // Well below the documented 51.2 s EOC-low interval but far above 160 ms.
  static constexpr uint32_t fullThresholdMs=5000;
  State state_=State::USB_ABSENT;
  bool low_=false,fullLatched_=false;
  uint32_t lowSince_=0;
  void reset(uint32_t now){state_=State::STARTUP;low_=false;fullLatched_=false;lowSince_=now;}
};
}

