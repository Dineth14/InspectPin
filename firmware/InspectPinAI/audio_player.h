#pragma once
#include <Arduino.h>
bool playWav(const String &path);
void setPlaybackVolume(uint8_t percent);
uint8_t playbackVolume();
bool recordingCue(bool starting);
namespace Amp { void begin(); void enable(bool on); void shutdownForSleep(); }
