#pragma once
#include <Arduino.h>
namespace Expander {
bool begin();
void tick();
bool available();
bool photoPressed();
bool askPressed();
bool setFlashlight(bool enabled);
bool setVibration(bool enabled);
bool setStatusLed(bool enabled);
bool setFaultLed(bool enabled);
bool inputLow(uint8_t bit);
bool prepareForSleep();
uint8_t latestPort();
}

