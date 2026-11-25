#pragma once
#include <ArduinoJson.h>

namespace FirmwareVersion {
const char *version();
const char *build();
const char *hardware();
void write(JsonObject out);
}
