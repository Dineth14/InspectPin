#include "battery_monitor.h"
#include "config.h"
void Battery::begin() { if (IP_BATTERY_ENABLED) { analogReadResolution(12); analogSetPinAttenuation(Config::battery,ADC_11db); } }
float Battery::volts() {
  if (!IP_BATTERY_ENABLED) return -1;
  uint32_t sum=0; for (int i=0;i<16;i++) { sum+=analogReadMilliVolts(Config::battery); delay(2); }
  return sum/16.0f/1000.0f*2.0f*IP_BATTERY_CALIBRATION;
}
bool Battery::low() { float v=volts(); return IP_BATTERY_ENABLED && v<IP_LOW_BATTERY_VOLTS; }
