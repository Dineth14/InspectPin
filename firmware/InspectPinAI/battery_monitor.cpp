#include "battery_monitor.h"
#include "config.h"
#include "battery_policy.h"
#include <Preferences.h>
namespace {
Battery::Reading current;
float smoothed=-1;
bool lowLatched=false,criticalLatched=false;
Preferences preferences;
float calibrationValue=IP_BATTERY_CALIBRATION;
bool preferencesOpen=false;
}
void Battery::begin() {
  preferencesOpen=preferences.begin("ip-battery",false);
  if(preferencesOpen) calibrationValue=preferences.getFloat("cal",IP_BATTERY_CALIBRATION);
  if(calibrationValue<0.8f||calibrationValue>1.2f) calibrationValue=IP_BATTERY_CALIBRATION;
  if (IP_BATTERY_ENABLED) { analogReadResolution(12); analogSetPinAttenuation(Config::battery,ADC_11db); sample(); }
}
Battery::Reading Battery::sample() {
  if (!IP_BATTERY_ENABLED) return current;
  uint16_t values[21];
  for (int i=0;i<21;i++) { values[i]=analogReadMilliVolts(Config::battery); delay(2); }
  for (int i=1;i<21;i++) { uint16_t x=values[i]; int j=i-1; while(j>=0&&values[j]>x){values[j+1]=values[j];j--;} values[j+1]=x; }
  float adcMv=BatteryPolicy::trimmedMean(values,21,4);
  float measured=adcMv/1000.0f*IP_BATTERY_DIVIDER_RATIO*calibrationValue;
  smoothed=smoothed<0?measured:0.8f*smoothed+0.2f*measured;
  lowLatched=BatteryPolicy::updateLowLatch(lowLatched,smoothed,IP_LOW_BATTERY_VOLTS,IP_BATTERY_HYSTERESIS_VOLTS);
  criticalLatched=BatteryPolicy::updateLowLatch(criticalLatched,smoothed,IP_CRITICAL_BATTERY_VOLTS,IP_BATTERY_HYSTERESIS_VOLTS);
  current={smoothed,BatteryPolicy::percentFromVoltage(smoothed),IP_BATTERY_UNCERTAINTY_VOLTS,
           smoothed>=2.5f&&smoothed<=4.5f,lowLatched,criticalLatched,millis()};
  return current;
}
Battery::Reading Battery::latest() { return current; }
float Battery::volts() { return sample().volts; }
bool Battery::low() { return IP_BATTERY_ENABLED && sample().low; }
bool Battery::critical() { return IP_BATTERY_ENABLED && sample().critical; }
float Battery::calibration() { return calibrationValue; }
bool Battery::setCalibration(float value) {
  if(value<0.8f||value>1.2f) return false;
  calibrationValue=value;
  return !preferencesOpen||preferences.putFloat("cal",value)==sizeof(float);
}
