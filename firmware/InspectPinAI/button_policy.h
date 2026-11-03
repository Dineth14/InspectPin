#pragma once
#include <stdint.h>

enum class ButtonAction : uint8_t { NONE, VOICE, CAMERA, SLEEP };

namespace ButtonPolicy {
constexpr uint32_t longPressMs=1200;
constexpr uint32_t powerHoldMs=1800;

inline ButtonAction voiceRelease(uint32_t heldMs,bool finalLayout) {
  return finalLayout&&heldMs>=longPressMs?ButtonAction::CAMERA:ButtonAction::VOICE;
}
inline ButtonAction secondRelease(uint32_t heldMs,bool finalLayout) {
  if(!finalLayout) return ButtonAction::CAMERA;
  return heldMs>=powerHoldMs?ButtonAction::SLEEP:ButtonAction::NONE;
}
inline ButtonAction resolve(ButtonAction voice,ButtonAction second) {
  if(second==ButtonAction::SLEEP) return second; // safety/power priority
  if(second==ButtonAction::CAMERA) return second;
  return voice;
}
}

