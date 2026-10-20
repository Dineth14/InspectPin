#pragma once
#include <Arduino.h>
#if __has_include("config.local.h")
#include "config.local.h"
#else
#include "config.example.h"
#endif
#ifndef IP_DEVICE_ID
#define IP_DEVICE_ID ""
#endif
#ifndef IP_CAMERA_BUTTON_ENABLED
#define IP_CAMERA_BUTTON_ENABLED false
#endif
namespace Config {
constexpr int micClock = 42, micData = 41;
constexpr int sdCS = 21, sdSCK = 7, sdMISO = 8, sdMOSI = 9;
constexpr int bclk = 1, ws = 2, dout = 4;
constexpr int button = 3, battery = 5, light = 43, haptic = 44;
constexpr int cameraButton = 6; // Board label D5, not GPIO5.
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
}
