#pragma once
#include "command_types.h"
#include "operation_guard.h"
#include "state_model.h"

struct DispatchDecision {
  bool accepted = false;
  const char *errorCode = "INVALID_COMMAND";
};

namespace CommandDispatcher {
DispatchDecision validate(const DeviceCommand &command,
                          const RuntimeState &state,
                          const OperationGuard &operation);
}

