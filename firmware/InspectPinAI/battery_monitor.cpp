#include "battery_monitor.h"
#include "config.h"
namespace {
Battery::Reading current;
float smoothed=-1;
bool lowLatched=false,criticalLatched=false;
float percentage(float v) {
  struct Point { float v,p; }; static const Point curve[]={
    {3.20f,0},{3.35f,5},{3.50f,12},{3.60f,25},{3.70f,50},{3.80f,70},{3.90f,85},{4.00f,94},{4.10f,98},{4.20f,100}};
  if (v<=curve[0].v) return 0; if (v>=curve[9].v) return 100;
  for (int i=1;i<10;i++) if (v<=curve[i].v)
    return curve[i-1].p+(v-curve[i-1].v)*(curve[i].p-curve[i-1].p)/(curve[i].v-curve[i-1].v);
  return -1;
}
}
void Battery::begin() {
  if (IP_BATTERY_ENABLED) { analogReadResolution(12); analogSetPinAttenuation(Config::battery,ADC_11db); sample(); }
}
Battery::Reading Battery::sample() {
  if (!IP_BATTERY_ENABLED) return current;
  uint16_t values[21];
  for (int i=0;i<21;i++) { values[i]=analogReadMilliVolts(Config::battery); delay(2); }
  for (int i=1;i<21;i++) { uint16_t x=values[i]; int j=i-1; while(j>=0&&values[j]>x){values[j+1]=values[j];j--;} values[j+1]=x; }
  uint32_t sum=0; for (int i=4;i<17;i++) sum+=values[i];
  float measured=sum/13.0f/1000.0f*2.0f*IP_BATTERY_CALIBRATION;
  smoothed=smoothed<0?measured:0.8f*smoothed+0.2f*measured;
  lowLatched=lowLatched?smoothed<IP_LOW_BATTERY_VOLTS+0.10f:smoothed<IP_LOW_BATTERY_VOLTS;
  criticalLatched=criticalLatched?smoothed<IP_CRITICAL_BATTERY_VOLTS+0.10f:smoothed<IP_CRITICAL_BATTERY_VOLTS;
  current={smoothed,percentage(smoothed),0.08f,smoothed>=2.5f&&smoothed<=4.5f,lowLatched,criticalLatched,millis()};
  return current;
}
Battery::Reading Battery::latest() { return current; }
float Battery::volts() { return sample().volts; }
bool Battery::low() { return IP_BATTERY_ENABLED && sample().low; }
bool Battery::critical() { return IP_BATTERY_ENABLED && sample().critical; }
