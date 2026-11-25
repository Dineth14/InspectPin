#pragma once
#include <Arduino.h>
#include <functional>
bool playWav(const String &path, const std::function<void(bool finishing)> &pollButtons = {});
void setPlaybackVolume(uint8_t percent);
uint8_t playbackVolume();
bool recordingCue(bool starting);
namespace Amp { void begin(); void enable(bool on); void shutdownForSleep(); }
