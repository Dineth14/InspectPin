#include "event_log.h"

namespace {
uint32_t eventCount = 0;
const char *eventName(EventCode code) {
  switch (code) {
    case EventCode::STATE_TRANSITION: return "STATE_TRANSITION";
    case EventCode::COMMAND_ACCEPTED: return "COMMAND_ACCEPTED";
    case EventCode::COMMAND_REJECTED: return "COMMAND_REJECTED";
    case EventCode::OPERATION_FAILED: return "OPERATION_FAILED";
    case EventCode::SLEEP_DEFERRED: return "SLEEP_DEFERRED";
    case EventCode::WAKE_REASON: return "WAKE_REASON";
  }
  return "UNKNOWN";
}
}

void EventLog::begin() { eventCount = 0; }
void EventLog::record(EventCode code, const String &detail) {
  ++eventCount;
  Serial.printf("EVENT %lu %s %s\n", static_cast<unsigned long>(eventCount),
                eventName(code), detail.c_str());
}
uint32_t EventLog::count() { return eventCount; }

