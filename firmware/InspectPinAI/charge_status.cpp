#include "charge_status.h"
#include "config.h"

namespace { ChargeStatus::Reading reading; }

const char *ChargeStatus::name(State value) {
  switch(value) {
    case State::CHARGING: return "charging";
    case State::FULL: return "full";
    case State::FAULT_UNSUPPORTED: return "fault_unsupported";
    default: return "unknown";
  }
}

void ChargeStatus::begin() {
  // Stock XIAO exposes no persistent full/fault signal to firmware. This stays
  // unknown until the separately powered decoder and its protected link exist.
  reading={false,State::UNKNOWN,"unavailable",millis(),0,false};
}
void ChargeStatus::tick() {
  reading.ageMs=millis()-reading.sampledAt;
}
ChargeStatus::Reading ChargeStatus::latest() {
  reading.ageMs=millis()-reading.sampledAt;
  return reading;
}

