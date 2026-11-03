#include <cassert>
#include "../InspectPinAI/battery_policy.h"
#include "../../hardware/charge_decoder/charge_decoder_logic.h"
#include "../InspectPinAI/button_policy.h"

int main(){
  assert(BatteryPolicy::percentFromVoltage(3.20f)==0.0f);
  assert(BatteryPolicy::percentFromVoltage(4.20f)==100.0f);
  const float mid=BatteryPolicy::percentFromVoltage(3.75f);
  assert(mid>59.9f&&mid<60.1f);
  assert(BatteryPolicy::updateLowLatch(false,3.39f,3.4f,0.1f));
  assert(BatteryPolicy::updateLowLatch(true,3.45f,3.4f,0.1f));
  assert(!BatteryPolicy::updateLowLatch(true,3.51f,3.4f,0.1f));
  uint16_t sorted[]={1,2,3,4,100};
  assert(BatteryPolicy::trimmedMean(sorted,5,1)==3.0f);

  ChargeDecoder::Controller decoder;
  assert(decoder.update(false,false,0).state==ChargeDecoder::State::USB_ABSENT);
  decoder.update(true,false,10);
  decoder.update(true,true,100);
  auto charging=decoder.update(true,false,260);
  assert(charging.state==ChargeDecoder::State::CHARGING);
  assert(decoder.update(true,false,500).ledOn==false);
  decoder.update(true,true,1000);
  auto full=decoder.update(true,true,6001);
  assert(full.state==ChargeDecoder::State::FULL&&full.ledOn);
  assert(decoder.update(true,false,7000).state==ChargeDecoder::State::FULL);
  assert(decoder.update(false,false,8000).state==ChargeDecoder::State::USB_ABSENT);
  assert(ButtonPolicy::voiceRelease(100,false)==ButtonAction::VOICE);
  assert(ButtonPolicy::voiceRelease(1300,true)==ButtonAction::CAMERA);
  assert(ButtonPolicy::secondRelease(100,false)==ButtonAction::CAMERA);
  assert(ButtonPolicy::secondRelease(100,true)==ButtonAction::NONE);
  assert(ButtonPolicy::secondRelease(1900,true)==ButtonAction::SLEEP);
  assert(ButtonPolicy::resolve(ButtonAction::VOICE,ButtonAction::SLEEP)==ButtonAction::SLEEP);
  return 0;
}
