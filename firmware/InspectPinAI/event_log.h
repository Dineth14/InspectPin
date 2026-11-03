#pragma once
#include <Arduino.h>

enum class EventCode : uint8_t {
  STATE_TRANSITION,
  COMMAND_ACCEPTED,
  COMMAND_REJECTED,
  OPERATION_FAILED,
  SLEEP_DEFERRED,
  WAKE_REASON
};

namespace EventLog {
void begin();
void record(EventCode code, const String &detail);
uint32_t count();
}

