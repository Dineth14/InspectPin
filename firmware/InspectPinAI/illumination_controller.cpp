#include "illumination_controller.h"
#include "config.h"
#include "status_feedback.h"
namespace { Illumination::State current; }
const char *Illumination::errorName(Error value){
  switch(value){case Error::FEATURE_DISABLED:return "LIGHT_FEATURE_DISABLED";case Error::LOW_BATTERY:return "LOW_BATTERY";case Error::INVALID_BRIGHTNESS:return "INVALID_BRIGHTNESS";default:return "";}
}
void Illumination::begin(){current={false,false,0,0,Error::NONE};Feedback::setLight(false);}
bool Illumination::set(bool enabled,int brightness,uint32_t timeoutMs,bool lowBattery,Error &error){
  current.requested=enabled;
  if(enabled&&!IP_LIGHT_ENABLED){error=Error::FEATURE_DISABLED;current.error=error;return false;}
  if(enabled&&lowBattery){forceOff();error=Error::LOW_BATTERY;current.error=error;return false;}
  if(brightness<0||brightness>255){error=Error::INVALID_BRIGHTNESS;current.error=error;return false;}
  current.actual=enabled;current.brightness=enabled?uint8_t(brightness):0;
  current.offAt=enabled&&timeoutMs?millis()+timeoutMs:0;current.error=Error::NONE;error=Error::NONE;
  Feedback::setLight(current.actual,current.brightness,timeoutMs);return true;
}
void Illumination::tick(bool lowBattery){
  if(current.actual&&(lowBattery||(current.offAt&&int32_t(millis()-current.offAt)>=0)))forceOff();
}
void Illumination::photoBegin(bool lowBattery){
  if(!IP_LIGHT_ENABLED)return;
  Error error;set(true,IP_LIGHT_DEFAULT_BRIGHTNESS,IP_LIGHT_TIMEOUT_MS,lowBattery,error);
}
void Illumination::photoEnd(){forceOff();}
void Illumination::forceOff(){current.requested=false;current.actual=false;current.brightness=0;current.offAt=0;Feedback::setLight(false);}
Illumination::State Illumination::state(){return current;}
