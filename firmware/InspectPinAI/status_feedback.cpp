#include "status_feedback.h"
#include "config.h"
namespace {
struct Pattern { uint8_t count,onMs,offMs; };
Pattern active{0,0,0}; uint8_t step=0; bool motorOn=false; uint32_t nextAt=0;
bool lamp=false; uint8_t lampBrightness=0; uint32_t lampOffAt=0;
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
void driveMotor(bool enabled) { motorOn=enabled; if(IP_HAPTIC_ENABLED) digitalWrite(Config::haptic,enabled?HIGH:LOW); }
void driveLight() {
  if(!IP_LIGHT_ENABLED) return;
  if(IP_LIGHT_PWM_ENABLED) ledcWrite(Config::light,lamp?lampBrightness:0);
  else digitalWrite(Config::light,lamp&&lampBrightness?HIGH:LOW);
}
}
void Feedback::begin() {
  if (IP_LIGHT_ENABLED) {
    if(IP_LIGHT_PWM_ENABLED) ledcAttach(Config::light,5000,8); else pinMode(Config::light,OUTPUT);
    lamp=false; lampBrightness=0; driveLight();
  }
  if (IP_HAPTIC_ENABLED) { pinMode(Config::haptic,OUTPUT); digitalWrite(Config::haptic,LOW); }
}
void Feedback::tick() {
  uint32_t now=millis();
  if(lamp&&lampOffAt&&int32_t(now-lampOffAt)>=0){lamp=false;lampOffAt=0;driveLight();}
  if(!active.count||int32_t(now-nextAt)<0) return;
  if(!motorOn) { driveMotor(true); nextAt=now+active.onMs; }
  else {
    driveMotor(false); step++;
    if(step>=active.count){active={0,0,0};step=0;}
    else nextAt=now+active.offMs;
  }
}
void Feedback::signal(Event event) { if(!IP_HAPTIC_ENABLED) return; active=pattern(event);step=0;driveMotor(false);nextAt=millis(); }
void Feedback::pulse() { signal(Event::READY); }
void Feedback::setLight(bool enabled,uint8_t brightness,uint32_t timeoutMs) {
  lamp=enabled; lampBrightness=enabled?brightness:0;
  lampOffAt=enabled&&timeoutMs?millis()+timeoutMs:0; driveLight();
}
void Feedback::illuminate(bool enabled) { setLight(enabled,IP_LIGHT_DEFAULT_BRIGHTNESS,enabled?IP_LIGHT_TIMEOUT_MS:0); }
bool Feedback::lightOn(){return lamp;}
uint8_t Feedback::lightBrightness(){return lampBrightness;}
