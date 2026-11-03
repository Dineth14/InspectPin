#pragma once
#include <stdint.h>

enum class ButtonAction : uint8_t { NONE, VOICE, CAMERA };

namespace ButtonPolicy {
inline ButtonAction voiceRelease(uint32_t) { return ButtonAction::VOICE; }
inline ButtonAction photoRelease(uint32_t) { return ButtonAction::CAMERA; }
inline ButtonAction resolve(ButtonAction voice,ButtonAction second) {
  if(second==ButtonAction::CAMERA) return second;
  return voice;
}
}

