#pragma once
#include <Arduino.h>
namespace Store {
bool begin();
String newPath(bool image);
bool markPending(const String &path, const String &job="");
bool nextPending(String &path, String &job);
void complete(const String &path);
bool selfTest();
}
