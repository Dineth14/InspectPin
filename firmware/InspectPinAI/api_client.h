#pragma once
#include <Arduino.h>
struct JobResult { String status, transcript, answer, error; bool audio=false; };
namespace Api {
bool upload(const String &path, String &job, String &error);
bool poll(const String &job, JobResult &result, String &error);
bool download(const String &job, const String &destination, String &error);
}
