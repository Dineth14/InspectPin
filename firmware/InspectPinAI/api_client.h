#pragma once
#include <Arduino.h>
#include "command_types.h"
struct JobResult { String status, transcript, answer, error; bool audio=false, hasCommand=false; DeviceCommand command; };
struct SessionContext {
  String imageId, contextId;
  uint32_t remainingMs=0;
  bool offlineRecording=false;
};
namespace Api {
String deviceId();
bool uploadRecording(const String &path, String &error);
bool upload(const String &path, String &job, String &error,
            const String &imageId="", const String &contextId="", String *returnedContext=nullptr);
bool uploadImage(const String &path, SessionContext &context, String &error);
bool session(SessionContext &context, String &error, bool clear=false);
bool poll(const String &job, JobResult &result, String &error);
bool download(const String &job, const String &destination, String &error);
bool heartbeat(const String &state, String &error);
bool pollRemoteCommand(DeviceCommand &command, String &remoteId, bool &available, String &error);
bool acknowledgeRemoteCommand(const String &remoteId, const String &status,
                              const String &actualState, const String &errorCode="");
}
