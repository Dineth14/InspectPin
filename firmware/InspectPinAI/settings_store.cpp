#include "settings_store.h"
#include <Preferences.h>
#include "config.h"

namespace {
Preferences preferences;
DeviceSettings current;
bool opened = false;
}

bool SettingsStore::begin() {
  current.volumePercent = 100;
  current.lightBrightness = IP_LIGHT_DEFAULT_BRIGHTNESS;
  current.hapticEnabled = false;
  current.idleTimeoutMs = IP_IDLE_TIMEOUT_MS;
  current.sound = {};
  opened = preferences.begin("inspectpin", false);
  if (!opened) return false;
  current.volumePercent = preferences.getUChar("volume", current.volumePercent);
  current.lightBrightness = preferences.getUChar("light", current.lightBrightness);
  current.hapticEnabled = preferences.getBool("haptic", current.hapticEnabled);
  current.idleTimeoutMs = preferences.getULong("idle_ms", current.idleTimeoutMs);
  const uint16_t sound=preferences.getUShort("sound", (65U<<8)|127U);
  if ((sound>>8)<=100 && (sound&255)<=127)
    current.sound={uint8_t(sound&255),uint8_t(sound>>8)};
  return true;
}

bool SettingsStore::updateSound(SoundFeedback::Settings sound) {
  if (!opened || sound.groups>127 || sound.volume>100) return false;
  const uint16_t encoded=(uint16_t(sound.volume)<<8)|sound.groups;
  if (preferences.putUShort("sound",encoded)!=sizeof(encoded)) return false;
  current.sound=sound;
  return true;
}

const DeviceSettings &SettingsStore::get() { return current; }

bool SettingsStore::update(const DeviceSettings &settings) {
  if (settings.volumePercent > 100) return false;
  current = settings;
  if (!opened) return false;
  return preferences.putUChar("volume", current.volumePercent) == 1 &&
         preferences.putUChar("light", current.lightBrightness) == 1 &&
         preferences.putBool("haptic", current.hapticEnabled) == 1 &&
         preferences.putULong("idle_ms", current.idleTimeoutMs) == sizeof(uint32_t);
}

void SettingsStore::end() {
  if (opened) preferences.end();
  opened = false;
}

