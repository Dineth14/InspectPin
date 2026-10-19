#pragma once
#include <Arduino.h>
struct JobResult { String status, transcript, answer, error; bool audio=false; };
struct SessionContext {
  String imageId, contextId;
  uint32_t remainingMs=0;
};
namespace Api {
String deviceId();
bool upload(const String &path, String &job, String &error,
            const String &imageId="", const String &contextId="", String *returnedContext=nullptr);
bool uploadImage(const String &path, SessionContext &context, String &error);
bool session(SessionContext &context, String &error, bool clear=false);
bool poll(const String &job, JobResult &result, String &error);
bool download(const String &job, const String &destination, String &error);
}
