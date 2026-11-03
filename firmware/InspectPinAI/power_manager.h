#pragma once
#include <Arduino.h>

namespace Power {
void begin();
void noteActivity();
void setIdleTimeout(uint32_t timeoutMs);
bool idleExpired();
bool enterLightSleep();
bool enterDeepSleep(const char *reason);
bool enterAutomaticSleep(const char *reason);
const char *wakeCause();
}
