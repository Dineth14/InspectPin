#include "ntc_monitor.h"
#include "config.h"
#include <cmath>
namespace { Ntc::Reading reading; }
void Ntc::begin(){if(IP_NTC_ENABLED){analogReadResolution(12);analogSetPinAttenuation(Config::ntc,ADC_11db);sample();}}
Ntc::Reading Ntc::sample(){
  if(!IP_NTC_ENABLED)return reading;
  uint32_t total=0;for(int i=0;i<16;i++){total+=analogReadMilliVolts(Config::ntc);delay(2);}const float mv=total/16.0f;
  reading={};reading.adcVolts=mv/1000.0f;reading.sampledAt=millis();reading.shortCircuit=mv<100;reading.openCircuit=mv>3200;
  if(!reading.shortCircuit&&!reading.openCircuit){reading.resistanceOhms=IP_NTC_FIXED_OHMS*mv/(3300.0f-mv);const float invT=1.0f/(IP_NTC_NOMINAL_C+273.15f)+logf(reading.resistanceOhms/IP_NTC_NOMINAL_OHMS)/IP_NTC_BETA;reading.celsius=1.0f/invT-273.15f;reading.valid=std::isfinite(reading.celsius)&&reading.celsius>-40&&reading.celsius<125;reading.safe=reading.valid&&reading.celsius>=IP_NTC_MIN_C&&reading.celsius<=IP_NTC_MAX_C;}
  return reading;
}
Ntc::Reading Ntc::latest(){return reading;}
