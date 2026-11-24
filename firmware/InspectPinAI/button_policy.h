#pragma once
#include <stdint.h>

enum class ButtonAction : uint8_t { NONE, VOICE, CAMERA, AUDIO_NOTE, VIDEO };

namespace ButtonPolicy {
inline ButtonAction voiceRelease(uint32_t held) { return held >= 2000 ? ButtonAction::AUDIO_NOTE : ButtonAction::VOICE; }
inline ButtonAction photoRelease(uint32_t held) { return held >= 2000 ? ButtonAction::VIDEO : ButtonAction::CAMERA; }
inline ButtonAction resolve(ButtonAction voice,ButtonAction second) {
  if(second!=ButtonAction::NONE) return second;
  return voice;
}
}

