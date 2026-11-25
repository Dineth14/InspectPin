#pragma once
#include <ArduinoJson.h>

namespace FirmwareVersion {
const char *version();
const char *build();
const char *hardware();
uint32_t releaseNumber();
void write(JsonObject out);
}
