#pragma once
#include <Arduino.h>
namespace Store {
bool begin();
void end();
String newPath(bool image);
String newVideoPath();
bool markPending(const String &path, const String &job="", const String &imageId="", const String &contextId="", bool unsent=true);
bool nextPending(String &path, String &job, String &imageId, String &contextId, bool automatic=false);
bool requireManualReplay(const String &path);
void complete(const String &path);
bool selfTest();
}
