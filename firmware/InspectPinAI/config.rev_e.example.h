#pragma once
// Reconciled Rev E candidate. Copy reviewed values into config.local.h only
// after schematic/ERC/continuity and wake tests pass.
#define IP_WIFI_SSID "YOUR_HOTSPOT"
#define IP_WIFI_PASSWORD ""
#define IP_SERVER_URL "http://YOUR_BACKEND_IP:5000"
#define IP_DEVICE_TOKEN ""
#define IP_DEVICE_ID ""
#define IP_RECORD_SECONDS 5
#define IP_PLAYBACK_GAIN 1.0f
#define IP_DEBUG true
#define IP_CAMERA_ENABLED true

#define IP_CAMERA_BUTTON_ENABLED false
#define IP_PCF8574_ENABLED true
#define IP_BATTERY_ENABLED true
#define IP_LIGHT_ENABLED true
#define IP_HAPTIC_ENABLED true
#define IP_CHARGE_DECODER_ENABLED true

#define IP_BATTERY_CALIBRATION 1.0f
#define IP_BATTERY_DIVIDER_RATIO 2.0f
#define IP_BATTERY_UNCERTAINTY_VOLTS 0.08f
#define IP_BATTERY_HYSTERESIS_VOLTS 0.10f
#define IP_LOW_BATTERY_VOLTS 3.40f
#define IP_CRITICAL_BATTERY_VOLTS 3.25f

// Automatic light sleep is the first validation target. Enable deep sleep only
// after PCF8574 INT retention/current and both existing-button wake paths pass.
#define IP_POWER_MANAGEMENT_ENABLED true
#define IP_DEEP_SLEEP_ENABLED false
#define IP_IDLE_TIMEOUT_MS 300000UL

// PCF8574 outputs are binary through fail-safe inverters in the reconciled design.
#define IP_LIGHT_PWM_ENABLED false
#define IP_LIGHT_DEFAULT_BRIGHTNESS 255
#define IP_LIGHT_TIMEOUT_MS 60000UL
#define IP_HAPTIC_PWM_ENABLED false
#define IP_HAPTIC_DEFAULT_INTENSITY 255
