#pragma once
#include <Arduino.h>
namespace Video {
struct Stats{bool active=false;String path,error;uint32_t frames=0,dropped=0,bytes=0,startedAt=0,elapsedMs=0;};
bool begin(const String &finalPath);
void tick(bool criticalBattery=false);
bool stop(const char *reason="requested");
bool active();
Stats stats();
void recoverIncomplete();
}

