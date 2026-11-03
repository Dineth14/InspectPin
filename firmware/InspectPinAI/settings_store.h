#pragma once
#include <Arduino.h>

struct DeviceSettings {
  uint8_t volumePercent = 100;
  uint8_t lightBrightness = 255;
  bool hapticEnabled = false;
  uint32_t idleTimeoutMs = 0;
};

namespace SettingsStore {
bool begin();
const DeviceSettings &get();
bool update(const DeviceSettings &settings);
void end();
}

