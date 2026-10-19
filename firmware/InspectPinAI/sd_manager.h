#pragma once
#include <Arduino.h>
namespace Store {
bool begin();
String newPath(bool image);
bool markPending(const String &path, const String &job="", const String &imageId="", const String &contextId="");
bool nextPending(String &path, String &job, String &imageId, String &contextId);
void complete(const String &path);
bool selfTest();
}
