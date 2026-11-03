#pragma once
#include <Arduino.h>

namespace Power {
void begin();
void noteActivity();
bool idleExpired();
bool enterLightSleep();
bool enterDeepSleep(const char *reason);
const char *wakeCause();
}
