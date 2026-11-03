#pragma once
// Copy to config.local.h and edit. Never commit real credentials.
#define IP_WIFI_SSID "YOUR_HOTSPOT"
#define IP_WIFI_PASSWORD ""
#define IP_SERVER_URL "http://172.20.10.3:5000"
#define IP_DEVICE_TOKEN ""
// Leave empty to identify this board by its unique eFuse MAC.
#define IP_DEVICE_ID ""
#define IP_RECORD_SECONDS 5
#define IP_PLAYBACK_GAIN 0.20f
#define IP_DEBUG true
#define IP_CAMERA_ENABLED true
// Legacy bench-only direct D5 camera button. Must be false for reconciled PCB,
// because D5/GPIO6 is exclusively the battery ADC.
#define IP_CAMERA_BUTTON_ENABLED false
#define IP_PCF8574_ENABLED false
#define IP_CHARGE_DECODER_ENABLED false
#define IP_BATTERY_ENABLED false
#define IP_LIGHT_ENABLED false
#define IP_HAPTIC_ENABLED false
#define IP_BATTERY_CALIBRATION 1.0f
#define IP_BATTERY_DIVIDER_RATIO 2.0f
#define IP_BATTERY_UNCERTAINTY_VOLTS 0.08f
#define IP_BATTERY_HYSTERESIS_VOLTS 0.10f
#define IP_LOW_BATTERY_VOLTS 3.4f
#define IP_CRITICAL_BATTERY_VOLTS 3.25f
// Keep disabled until ASK/PCF-INT wake wiring and measured sleep current pass.
#define IP_POWER_MANAGEMENT_ENABLED false
#define IP_DEEP_SLEEP_ENABLED false
#define IP_POWER_BUTTON_PIN 5
#define IP_IDLE_TIMEOUT_MS 0UL
#define IP_LIGHT_PWM_ENABLED false
#define IP_LIGHT_DEFAULT_BRIGHTNESS 255
#define IP_LIGHT_TIMEOUT_MS 60000UL
#define IP_HAPTIC_PWM_ENABLED false
#define IP_HAPTIC_DEFAULT_INTENSITY 180
