#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>
#include <functional>
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
bool firmwareRequest(const String &route, const JsonDocument &payload, JsonDocument &reply);
bool streamFirmware(const String &id,size_t size,
                    const std::function<bool(const uint8_t *,size_t)> &consume);
}
