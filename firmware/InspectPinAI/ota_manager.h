#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>

namespace OtaManager {
bool enabled();
String origin();
const char *ca();
const char *lastResult();
void verifyBoot(bool settingsReady, bool storageReady);
void service();
}
