#pragma once
#include "state_model.h"

class OperationGuard {
 public:
  bool begin(OperationClass value) { if (active_!=OperationClass::IDLE) return false; active_=value; return true; }
  void transition(OperationClass value) { active_=value; }
  void end() { active_=OperationClass::IDLE; }
  bool busy() const { return active_!=OperationClass::IDLE; }
  bool sleepSafe() const { return active_==OperationClass::IDLE; }
  bool cancellable() const { return active_==OperationClass::AI_WAIT || active_==OperationClass::NETWORK || active_==OperationClass::VIDEO; }
  OperationClass active() const { return active_; }
 private: OperationClass active_=OperationClass::IDLE;
};
