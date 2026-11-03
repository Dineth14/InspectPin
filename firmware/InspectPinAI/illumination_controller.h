#pragma once
#include <Arduino.h>
namespace Illumination {
enum class Error : uint8_t { NONE, FEATURE_DISABLED, LOW_BATTERY, INVALID_BRIGHTNESS };
struct State { bool requested=false, actual=false; uint8_t brightness=0; uint32_t offAt=0; Error error=Error::NONE; };
void begin();
void tick(bool lowBattery=false);
bool set(bool enabled,int brightness,uint32_t timeoutMs,bool lowBattery,Error &error);
void photoBegin(bool lowBattery);
void photoEnd();
void forceOff();
State state();
const char *errorName(Error value);
}

