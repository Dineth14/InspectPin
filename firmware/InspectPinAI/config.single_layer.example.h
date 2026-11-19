#pragma once
// Single-layer PCB profile. Build with -DIP_USE_SINGLE_LAYER_CONFIG.
// Copy to config.local.h (gitignored) and add credentials for deployment.
#define IP_WIFI_SSID "YOUR_HOTSPOT"
#define IP_WIFI_PASSWORD ""
#define IP_SERVER_URL "http://192.168.1.2:5000"
#define IP_DEVICE_TOKEN ""
#define IP_DEVICE_ID ""
#define IP_RECORD_SECONDS 5
#define IP_PLAYBACK_GAIN 1.0f
#define IP_DEBUG true
#define IP_CAMERA_ENABLED true
#define IP_CAMERA_BUTTON_ENABLED true   // PHOTO = GPIO44 (D7)
#define IP_PCF8574_ENABLED false
#define IP_BATTERY_ENABLED false        // no battery sense on this PCB
#define IP_LIGHT_ENABLED false
#define IP_HAPTIC_ENABLED false
#define IP_BATTERY_CALIBRATION 1.0f
#define IP_LOW_BATTERY_VOLTS 3.4f
#define IP_POWER_MANAGEMENT_ENABLED true
#define IP_DEEP_SLEEP_ENABLED true      // ASK (GPIO5) wakes from deep sleep
#define IP_IDLE_TIMEOUT_MS 300000UL     // 300 s / 5 min inactivity
