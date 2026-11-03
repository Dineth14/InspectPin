#pragma once
#include <stdint.h>

// Pure state contract: this header deliberately has no Arduino dependencies so
// the transition and safety rules can be tested on a host compiler.
enum class TopLevelState : uint8_t {
  DEEP_SLEEP,
  LIGHT_SLEEP,
  BOOTING,
  INITIALIZING,
  ACTIVE,
  ERROR,
  RECOVERY
};

enum class ActiveState : uint8_t {
  NONE,
  READY,
  VOICE_LISTENING,
  AUDIO_RECORDING,
  IMAGE_CAPTURE,
  VIDEO_RECORDING,
  MEDIA_SAVING,
  WIFI_CONNECTING,
  UPLOADING,
  AI_PROCESSING,
  DOWNLOADING,
  AUDIO_PLAYBACK
};

enum class OperationClass : uint8_t {
  IDLE,
  CAPTURE,
  MEDIA_WRITE,
  NETWORK,
  AI_WAIT,
  PLAYBACK,
  VIDEO,
  RECOVERY
};

struct StatusFlags {
  bool connected = false;
  bool lowBattery = false;
  bool criticalBattery = false;
  bool lightOn = false;
  bool hapticEnabled = false;
  bool chargingKnown = false;
};

struct RuntimeState {
  TopLevelState top = TopLevelState::BOOTING;
  ActiveState active = ActiveState::NONE;
  StatusFlags flags{};
};

constexpr bool isBusyActiveState(ActiveState state) {
  return state != ActiveState::NONE && state != ActiveState::READY;
}

constexpr bool isCriticalOperation(OperationClass operation) {
  return operation == OperationClass::MEDIA_WRITE ||
         operation == OperationClass::PLAYBACK ||
         operation == OperationClass::VIDEO;
}

constexpr bool canEnterSleep(const RuntimeState &state, OperationClass operation) {
  return state.top != TopLevelState::INITIALIZING &&
         state.top != TopLevelState::DEEP_SLEEP &&
         operation == OperationClass::IDLE &&
         !isBusyActiveState(state.active);
}

constexpr bool validTopTransition(TopLevelState from, TopLevelState to) {
  if (from == to) return true;
  switch (from) {
    case TopLevelState::BOOTING:
      return to == TopLevelState::INITIALIZING || to == TopLevelState::ERROR;
    case TopLevelState::INITIALIZING:
      return to == TopLevelState::ACTIVE || to == TopLevelState::ERROR ||
             to == TopLevelState::RECOVERY;
    case TopLevelState::ACTIVE:
      return to == TopLevelState::ERROR || to == TopLevelState::RECOVERY ||
             to == TopLevelState::LIGHT_SLEEP || to == TopLevelState::DEEP_SLEEP;
    case TopLevelState::ERROR:
      return to == TopLevelState::RECOVERY || to == TopLevelState::ACTIVE ||
             to == TopLevelState::DEEP_SLEEP;
    case TopLevelState::RECOVERY:
      return to == TopLevelState::ACTIVE || to == TopLevelState::ERROR ||
             to == TopLevelState::DEEP_SLEEP;
    case TopLevelState::LIGHT_SLEEP:
      return to == TopLevelState::ACTIVE || to == TopLevelState::DEEP_SLEEP ||
             to == TopLevelState::ERROR;
    case TopLevelState::DEEP_SLEEP:
      return to == TopLevelState::BOOTING;  // Only a reset/wake begins execution.
  }
  return false;
}

class StateController {
 public:
  const RuntimeState &current() const { return state_; }

  bool transitionTop(TopLevelState next) {
    if (!validTopTransition(state_.top, next)) return false;
    state_.top = next;
    if (next != TopLevelState::ACTIVE) state_.active = ActiveState::NONE;
    return true;
  }

  bool transitionActive(ActiveState next) {
    if (state_.top != TopLevelState::ACTIVE) return false;
    state_.active = next;
    return true;
  }

  void setFlags(const StatusFlags &flags) { state_.flags = flags; }
  StatusFlags &flags() { return state_.flags; }

 private:
  RuntimeState state_{};
};

