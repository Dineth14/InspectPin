#pragma once
#include "button_manager.h"
enum class AppState { BOOT, INITIALIZING, READY, RECORDING, SAVING, UPLOADING, WAITING_FOR_AI, DOWNLOADING, PLAYING, OFFLINE, RETRYING, ERROR, LOW_BATTERY };
class App {
 public: void begin(); void tick();
 private:
  AppState state_=AppState::BOOT;
  ButtonManager button_;
  String path_,job_,answerPath_;
  bool sdReady_=false;
  uint32_t lastPoll_=0,jobStart_=0,retryAt_=0,lastBattery_=0;
  unsigned attempts_=0;
  void state(AppState value);
  void fail(const String &error, bool offline=false);
  void capture(bool image);
  void retry();
  bool idle() const;
};
