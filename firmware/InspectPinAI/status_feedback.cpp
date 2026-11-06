#include "status_feedback.h"
#include "config.h"
#include "pcf8574_manager.h"
namespace {
struct Pattern { uint8_t count,onMs,offMs; };
Pattern active{0,0,0}; uint8_t step=0; bool motorOn=false; uint32_t nextAt=0;
bool lamp=false; uint8_t lampBrightness=0; uint32_t lampOffAt=0;
Feedback::Event queue[8]; uint8_t queueHead=0,queueTail=0,queueCount=0;
bool hapticAllowed=IP_HAPTIC_ENABLED; uint8_t hapticLevel=IP_HAPTIC_DEFAULT_INTENSITY;
Pattern pattern(Feedback::Event e) {
  switch(e) {
    case Feedback::Event::ERROR: return {3,80,80};
    case Feedback::Event::WIFI_LOST: return {2,120,160};
    case Feedback::Event::LOW_BATTERY: return {3,160,240};
    case Feedback::Event::VIDEO_STARTED: return {2,60,100};
    case Feedback::Event::VIDEO_STOPPED: return {2,120,80};
    case Feedback::Event::ANSWER_READY: return {2,50,60};
    default: return {1,60,0};
  }
}
void driveMotor(bool enabled) {
  motorOn=enabled;
  if(!IP_HAPTIC_ENABLED) return;
  if(IP_PCF8574_ENABLED){Expander::setVibration(enabled&&hapticAllowed);return;}
  if(IP_HAPTIC_PWM_ENABLED) ledcWrite(Config::haptic,enabled&&hapticAllowed?hapticLevel:0);
  else digitalWrite(Config::haptic,enabled&&hapticAllowed?HIGH:LOW);
}
void driveLight() {
  if(!IP_LIGHT_ENABLED) return;
  if(IP_LIGHT_ON_PCF8574){Expander::setFlashlight(lamp&&lampBrightness);return;}
  if(IP_LIGHT_PWM_ENABLED) ledcWrite(Config::light,lamp?lampBrightness:0);
  else digitalWrite(Config::light,lamp&&lampBrightness?HIGH:LOW);
}
}
void Feedback::begin() {
  if (IP_LIGHT_ENABLED) {
    if(!IP_LIGHT_ON_PCF8574){if(IP_LIGHT_PWM_ENABLED) ledcAttach(Config::light,5000,8); else pinMode(Config::light,OUTPUT);}
    lamp=false; lampBrightness=0; driveLight();
  }
  if (IP_HAPTIC_ENABLED) {
    if(!IP_PCF8574_ENABLED){if(IP_HAPTIC_PWM_ENABLED) ledcAttach(Config::haptic,200,8); else pinMode(Config::haptic,OUTPUT);}
    driveMotor(false);
  }
}
void Feedback::tick() {
  uint32_t now=millis();
  if(lamp&&lampOffAt&&int32_t(now-lampOffAt)>=0){lamp=false;lampOffAt=0;driveLight();}
  if(!active.count&&queueCount){active=pattern(queue[queueHead]);queueHead=(queueHead+1)%8;queueCount--;step=0;nextAt=now;}
  if(!active.count||int32_t(now-nextAt)<0) return;
  if(!motorOn) { driveMotor(true); nextAt=now+active.onMs; }
  else {
    driveMotor(false); step++;
    if(step>=active.count){active={0,0,0};step=0;}
    else nextAt=now+active.offMs;
  }
}
void Feedback::signal(Event event) {
  if(!IP_HAPTIC_ENABLED||!hapticAllowed) return;
  if(queueCount>=8){Serial.println("Haptic queue full; event dropped");return;}
  queue[queueTail]=event;queueTail=(queueTail+1)%8;queueCount++;
}
void Feedback::pulse() { signal(Event::READY); }
void Feedback::setLight(bool enabled,uint8_t brightness,uint32_t timeoutMs) {
  lamp=enabled; lampBrightness=enabled?brightness:0;
  lampOffAt=enabled&&timeoutMs?millis()+timeoutMs:0; driveLight();
}
void Feedback::illuminate(bool enabled) { setLight(enabled,IP_LIGHT_DEFAULT_BRIGHTNESS,enabled?IP_LIGHT_TIMEOUT_MS:0); }
bool Feedback::lightOn(){return lamp;}
uint8_t Feedback::lightBrightness(){return lampBrightness;}
void Feedback::setHaptic(bool enabled,uint8_t intensity){hapticAllowed=enabled;hapticLevel=intensity;if(!enabled)driveMotor(false);}
bool Feedback::hapticEnabled(){return IP_HAPTIC_ENABLED&&hapticAllowed;}
uint8_t Feedback::hapticIntensity(){return hapticLevel;}
