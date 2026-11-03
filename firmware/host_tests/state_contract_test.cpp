#include <cassert>
#include "../InspectPinAI/state_model.h"

int main() {
  StateController state;
  assert(state.current().top == TopLevelState::BOOTING);
  assert(!state.transitionTop(TopLevelState::ACTIVE));
  assert(state.transitionTop(TopLevelState::INITIALIZING));
  assert(!state.transitionActive(ActiveState::READY));
  assert(state.transitionTop(TopLevelState::ACTIVE));
  assert(state.transitionActive(ActiveState::READY));
  assert(canEnterSleep(state.current(), OperationClass::IDLE));
  assert(state.transitionActive(ActiveState::MEDIA_SAVING));
  assert(!canEnterSleep(state.current(), OperationClass::MEDIA_WRITE));
  assert(isCriticalOperation(OperationClass::MEDIA_WRITE));
  assert(isCriticalOperation(OperationClass::VIDEO));
  assert(state.transitionTop(TopLevelState::ERROR));
  assert(state.current().active == ActiveState::NONE);
  assert(state.transitionTop(TopLevelState::RECOVERY));
  assert(state.transitionTop(TopLevelState::ACTIVE));
  assert(!validTopTransition(TopLevelState::ACTIVE, TopLevelState::BOOTING));
  return 0;
}
