#pragma once
#include <Arduino.h>

enum class CommandSource : uint8_t { BUTTON, SERIAL_CONSOLE, VOICE, BLE, HTTP, INTERNAL };
enum class CommandType : uint8_t {
  NONE, STATUS_GET, VOICE_START, CANCEL, PHOTO_CAPTURE, VIDEO_START, VIDEO_STOP,
  LIGHT_SET, VOLUME_SET, HAPTIC_SET, BATTERY_GET, MEDIA_LIST, MEDIA_DELETE,
  SLEEP, RESTART, SETTINGS_GET, SETTINGS_PATCH, RETRY, CONTEXT_GET,
  CONTEXT_CLEAR, SD_TEST, WIFI_CONNECT, CAMERA_DIAGNOSTIC, TONE_PLAY, MEDIA_DOWNLOAD
};
enum class CommandStatus : uint8_t { REJECTED, ACCEPTED, RUNNING, COMPLETED, FAILED, CANCELLED };

struct DeviceCommand {
  CommandType type=CommandType::NONE;
  CommandSource source=CommandSource::INTERNAL;
  String requestId;
  String stringValue;
  int32_t intValue=0;
  bool boolValue=false;
};

struct CommandResult {
  String requestId;
  CommandStatus status=CommandStatus::REJECTED;
  String errorCode;
  String actualState;
};

namespace Commands {
DeviceCommand fromSerial(char value);
const char *name(CommandType value);
CommandType fromName(const String &value);
}
