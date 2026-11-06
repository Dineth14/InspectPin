#pragma once
#include <Arduino.h>
#if defined(IP_USE_REV_N_CONFIG)
#include "config.revn.example.h"
#elif defined(IP_USE_REV_E_CANDIDATE_CONFIG)
#include "config.rev_e.example.h"
#elif __has_include("config.local.h")
#include "config.local.h"
#else
#include "config.example.h"
#endif
#include "hardware_profile.h"
#ifndef IP_DEVICE_ID
#define IP_DEVICE_ID ""
#endif
#ifndef IP_CAMERA_BUTTON_ENABLED
#define IP_CAMERA_BUTTON_ENABLED false
#endif
#ifndef IP_POWER_MANAGEMENT_ENABLED
#define IP_POWER_MANAGEMENT_ENABLED false
#endif
#ifndef IP_DEEP_SLEEP_ENABLED
#define IP_DEEP_SLEEP_ENABLED false
#endif
#ifndef IP_PCF8574_ENABLED
#define IP_PCF8574_ENABLED false
#endif
#ifndef IP_CHARGE_DECODER_ENABLED
#define IP_CHARGE_DECODER_ENABLED false
#endif
#ifndef IP_IDLE_TIMEOUT_MS
#define IP_IDLE_TIMEOUT_MS 0UL
#endif
#ifndef IP_CRITICAL_BATTERY_VOLTS
#define IP_CRITICAL_BATTERY_VOLTS 3.25f
#endif
#ifndef IP_LIGHT_PWM_ENABLED
#define IP_LIGHT_PWM_ENABLED false
#endif
#ifndef IP_LIGHT_DEFAULT_BRIGHTNESS
#define IP_LIGHT_DEFAULT_BRIGHTNESS 255
#endif
#ifndef IP_LIGHT_TIMEOUT_MS
#define IP_LIGHT_TIMEOUT_MS 60000UL
#endif
#ifndef IP_BATTERY_DIVIDER_RATIO
#define IP_BATTERY_DIVIDER_RATIO 2.0f
#endif
#ifndef IP_BATTERY_UNCERTAINTY_VOLTS
#define IP_BATTERY_UNCERTAINTY_VOLTS 0.08f
#endif
#ifndef IP_BATTERY_HYSTERESIS_VOLTS
#define IP_BATTERY_HYSTERESIS_VOLTS 0.10f
#endif
#ifndef IP_HAPTIC_PWM_ENABLED
#define IP_HAPTIC_PWM_ENABLED false
#endif
#ifndef IP_HAPTIC_DEFAULT_INTENSITY
#define IP_HAPTIC_DEFAULT_INTENSITY 180
#endif
#ifndef IP_LIGHT_ON_PCF8574
#define IP_LIGHT_ON_PCF8574 true
#endif
#ifndef IP_INA219_ENABLED
#define IP_INA219_ENABLED false
#endif
#ifndef IP_NTC_ENABLED
#define IP_NTC_ENABLED false
#endif
#ifndef IP_REV_N_STATUS_LEDS_ENABLED
#define IP_REV_N_STATUS_LEDS_ENABLED false
#endif
#ifndef IP_INA219_SHUNT_OHMS
#define IP_INA219_SHUNT_OHMS 0.1f
#endif
#ifndef IP_INA219_CURRENT_LSB_AMPS
#define IP_INA219_CURRENT_LSB_AMPS 0.0001f
#endif
#ifndef IP_NTC_FIXED_OHMS
#define IP_NTC_FIXED_OHMS 10000.0f
#endif
#ifndef IP_NTC_NOMINAL_OHMS
#define IP_NTC_NOMINAL_OHMS 10000.0f
#endif
#ifndef IP_NTC_BETA
#define IP_NTC_BETA 3950.0f
#endif
#ifndef IP_NTC_NOMINAL_C
#define IP_NTC_NOMINAL_C 25.0f
#endif
#ifndef IP_NTC_MIN_C
#define IP_NTC_MIN_C 0.0f
#endif
#ifndef IP_NTC_MAX_C
#define IP_NTC_MAX_C 45.0f
#endif
#ifndef IP_USB_PRESENT_AVAILABLE
#define IP_USB_PRESENT_AVAILABLE false
#endif
#ifndef IP_NCHG_AVAILABLE
#define IP_NCHG_AVAILABLE false
#endif
namespace Config {
constexpr int micClock = 42, micData = 41;
constexpr int sdCS = 21, sdSCK = 7, sdMISO = 8, sdMOSI = 9;
constexpr int bclk = HardwareProfile::speakerBclkGpio;
constexpr int ws = HardwareProfile::speakerLrclkGpio;
constexpr int dout = HardwareProfile::speakerDataGpio;
constexpr int button = HardwareProfile::askButtonGpio;
constexpr int battery = HardwareProfile::batteryAdcGpio;
constexpr int pcfInterrupt = HardwareProfile::pcfInterruptGpio;
// Legacy direct pins exist only for old bench builds. Reconciled hardware uses
// PCF8574 P0/P1 through fail-safe inverters and PHOTO on P3.
constexpr int light = HardwareProfile::flashlightGpio, haptic = HardwareProfile::hapticGpio, cameraButton = 6;
constexpr int ntc = HardwareProfile::ntcGpio;
constexpr uint32_t sampleRate = 16000;
constexpr uint32_t recordSeconds = IP_RECORD_SECONDS;
constexpr uint32_t wifiTimeoutMs = 15000, httpTimeoutMs = 10000;
constexpr uint32_t pollIntervalMs = 2000, jobTimeoutMs = 240000;
constexpr size_t maxAnswerBytes = 3840044;  // 120 seconds of PCM16 mono
constexpr float playbackGain = IP_PLAYBACK_GAIN;
static_assert(recordSeconds > 0 && recordSeconds <= 30, "Record duration must be 1..30 seconds");
// The backend already peak-limits generated speech to 25% of PCM16 full scale.
// Allow unity playback so the firmware does not attenuate that bounded signal again.
static_assert(playbackGain >= 0 && playbackGain <= 1.0f, "Playback gain must be in the range 0..1");
static_assert(HardwareProfile::pcfInterruptGpio==-1 ||
              (HardwareProfile::pcfInterruptGpio>=0 && HardwareProfile::pcfInterruptGpio<=21),
              "PCF interrupt must be absent or on an ESP32-S3 RTC wake GPIO");
static_assert(IP_LIGHT_DEFAULT_BRIGHTNESS>=0 && IP_LIGHT_DEFAULT_BRIGHTNESS<=255, "Brightness must be 0..255");
static_assert(IP_BATTERY_DIVIDER_RATIO>1.0f && IP_BATTERY_DIVIDER_RATIO<10.0f, "Invalid battery divider ratio");
static_assert(IP_HAPTIC_DEFAULT_INTENSITY>=0 && IP_HAPTIC_DEFAULT_INTENSITY<=255, "Haptic intensity must be 0..255");
static_assert(!(IP_BATTERY_ENABLED && IP_CAMERA_BUTTON_ENABLED),
              "D5/GPIO6 cannot be both battery ADC and legacy PHOTO button");
static_assert(!(IP_PCF8574_ENABLED && IP_CAMERA_BUTTON_ENABLED),
              "Use PCF8574 P3 PHOTO or legacy direct PHOTO, never both");
#if defined(IP_USE_REV_N_CONFIG)
static_assert(button < 0, "Rev N ASK is on PCF8574; GPIO3 is reserved");
static_assert(bclk == 43 && ws == 44 && dout == 2, "Rev N MAX98357A pin mismatch");
static_assert(light == 4 && ntc == 1, "Rev N flashlight/NTC pin mismatch");
#endif
}
