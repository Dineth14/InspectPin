#pragma once
#include <Arduino.h>
bool playWav(const String &path);
void setPlaybackVolume(uint8_t percent);
uint8_t playbackVolume();
