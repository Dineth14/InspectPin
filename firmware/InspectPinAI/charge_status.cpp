#include "charge_status.h"
#include "config.h"
#include "pcf8574_manager.h"
#include "hardware_profile.h"

namespace {
ChargeStatus::Reading reading;
uint32_t ledChanged=0;
bool green=false,fault=false;
void drive(bool greenOn,bool faultOn){
  if(!IP_REV_N_STATUS_LEDS_ENABLED||!Expander::available())return;
  if(green!=greenOn){green=greenOn;Expander::setStatusLed(green);}
  if(fault!=faultOn){fault=faultOn;Expander::setFaultLed(fault);}
}
}

const char *ChargeStatus::name(State value) {
  switch(value) {
    case State::CHARGING: return "charging";
    case State::FULL: return "full";
    case State::FAULT_UNSUPPORTED: return "fault_unsupported";
    default: return "unknown";
  }
}

void ChargeStatus::begin() {
  // Stock XIAO exposes no persistent full/fault signal to firmware. This stays
  // unknown until the separately powered decoder and its protected link exist.
  reading={false,State::UNKNOWN,"unavailable",millis(),0,false};
  drive(false,false);
}
void ChargeStatus::tick() {
  if(IP_CHARGE_DECODER_ENABLED&&Expander::available()){
    const bool usb=IP_USB_PRESENT_AVAILABLE&&Expander::inputLow(HardwareProfile::pcfUsbPresentN);
    reading.usbPresent=usb;reading.valid=usb&&IP_NCHG_AVAILABLE;
    reading.source=!usb?"usb_detector":(IP_NCHG_AVAILABLE?"verified_nchg_tap":"usb_only_no_verified_nchg");
    if(!usb)reading.state=State::UNKNOWN;
    else if(!IP_NCHG_AVAILABLE)reading.state=State::UNKNOWN;
    else reading.state=Expander::inputLow(HardwareProfile::pcfChargeN)?State::FULL:State::CHARGING;
    reading.sampledAt=millis();
  }
  reading.ageMs=millis()-reading.sampledAt;
  const uint32_t now=millis();
  if(!reading.usbPresent)drive(false,false);
  else if(!reading.valid){if(now-ledChanged>=125){ledChanged=now;drive(false,!fault);}}
  else if(reading.state==State::FULL)drive(true,false);
  else if(reading.state==State::CHARGING){if(now-ledChanged>=500){ledChanged=now;drive(!green,false);}}
}
ChargeStatus::Reading ChargeStatus::latest() {
  reading.ageMs=millis()-reading.sampledAt;
  return reading;
}

