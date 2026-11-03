#include "command_dispatcher.h"

DispatchDecision CommandDispatcher::validate(const DeviceCommand &command,
                                               const RuntimeState &state,
                                               const OperationGuard &operation) {
  if (command.type == CommandType::NONE) return {false, "INVALID_COMMAND"};
  if (!command.requestId.length()) return {false, "REQUEST_ID_REQUIRED"};

  const bool stopOrCancel = command.type == CommandType::CANCEL ||
                            command.type == CommandType::VIDEO_STOP;
  const bool observational = command.type == CommandType::STATUS_GET ||
                             command.type == CommandType::BATTERY_GET ||
                             command.type == CommandType::CONTEXT_GET;
  if (state.top == TopLevelState::INITIALIZING && !observational)
    return {false, "INITIALIZING"};
  if (state.flags.criticalBattery && command.type != CommandType::SLEEP &&
      command.type != CommandType::STATUS_GET && command.type != CommandType::BATTERY_GET)
    return {false, "CRITICAL_BATTERY"};
  if (operation.busy() && !stopOrCancel && !observational)
    return {false, "DEVICE_BUSY"};
  if (command.type == CommandType::SLEEP && !canEnterSleep(state, operation.active()))
    return {false, "SLEEP_DEFERRED"};
  if (command.type == CommandType::VIDEO_STOP && operation.active() != OperationClass::VIDEO)
    return {false, "VIDEO_NOT_RECORDING"};
  return {true, ""};
}

