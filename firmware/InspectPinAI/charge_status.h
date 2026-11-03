#pragma once
#include <Arduino.h>

namespace ChargeStatus {
enum class State : uint8_t { UNKNOWN, CHARGING, FULL, FAULT_UNSUPPORTED };
struct Reading {
  bool usbPresent = false;
  State state = State::UNKNOWN;
  const char *source = "unavailable";
  uint32_t sampledAt = 0;
  uint32_t ageMs = 0;
  bool valid = false;
};
void begin();
void tick();
Reading latest();
const char *name(State value);
}

