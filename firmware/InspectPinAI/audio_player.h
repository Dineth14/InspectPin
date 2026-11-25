#pragma once
#include <Arduino.h>
#include <functional>
// The application task owns the speaker and microphone through this guard.
class AudioLease {
 public:
  AudioLease();
  ~AudioLease();
  AudioLease(const AudioLease &)=delete;
  AudioLease &operator=(const AudioLease &)=delete;
  explicit operator bool() const { return acquired_; }
 private:
  bool acquired_;
};
bool playPcm(const std::function<size_t(int16_t *, size_t)> &fill);
bool playWav(const String &path, const std::function<void(bool finishing)> &pollButtons = {});
void setPlaybackVolume(uint8_t percent);
uint8_t playbackVolume();
namespace Amp { void begin(); void enable(bool on); void shutdownForSleep(); }
