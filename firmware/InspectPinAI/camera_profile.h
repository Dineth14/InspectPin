#pragma once

#define INSPECTPIN_CAMERA_PROFILE_OPTIMIZED 1
#define INSPECTPIN_CAMERA_PROFILE_LOW_LIGHT_TEST 2

#ifndef IP_CAMERA_PROFILE
#define IP_CAMERA_PROFILE INSPECTPIN_CAMERA_PROFILE_OPTIMIZED
#endif
#ifndef IP_CAMERA_XCLK_HZ
#define IP_CAMERA_XCLK_HZ 20000000
#endif
#ifndef IP_CAMERA_JPEG_QUALITY
#define IP_CAMERA_JPEG_QUALITY 12
#endif
#ifndef IP_CAMERA_BRIGHTNESS
#define IP_CAMERA_BRIGHTNESS 1
#endif
#ifndef IP_CAMERA_CONTRAST
#define IP_CAMERA_CONTRAST 0
#endif
#ifndef IP_CAMERA_SATURATION
// The original tuned /status JSON is unavailable. -2 is provisional and is
// also the installed official OV3660 CameraWebServer startup value.
#define IP_CAMERA_SATURATION -2
#endif
#ifndef IP_CAMERA_SHARPNESS
#define IP_CAMERA_SHARPNESS 1
#endif
#ifndef IP_CAMERA_DENOISE
#define IP_CAMERA_DENOISE 5
#endif
#ifndef IP_CAMERA_AE_LEVEL
#define IP_CAMERA_AE_LEVEL 0
#endif
#ifndef IP_CAMERA_GAIN_CEILING
// -1 preserves the initialized value. Use 0..6 only after recovering the exact
// gainceiling field from the original tuned CameraWebServer /status response.
#define IP_CAMERA_GAIN_CEILING -1
#endif
#ifndef IP_CAMERA_SETTLE_MS
#define IP_CAMERA_SETTLE_MS 500
#endif
#ifndef IP_CAMERA_WARMUP_FRAMES
#define IP_CAMERA_WARMUP_FRAMES 2
#endif
#ifndef IP_CAMERA_LOW_LIGHT_AE_LEVEL
#define IP_CAMERA_LOW_LIGHT_AE_LEVEL 1
#endif
#ifndef IP_CAMERA_LOW_LIGHT_SETTLE_MS
#define IP_CAMERA_LOW_LIGHT_SETTLE_MS 1000
#endif
#ifndef IP_CAMERA_LOW_LIGHT_WARMUP_FRAMES
#define IP_CAMERA_LOW_LIGHT_WARMUP_FRAMES 4
#endif

static_assert(IP_CAMERA_PROFILE == INSPECTPIN_CAMERA_PROFILE_OPTIMIZED ||
              IP_CAMERA_PROFILE == INSPECTPIN_CAMERA_PROFILE_LOW_LIGHT_TEST,
              "Unknown InspectPin camera profile");
static_assert(IP_CAMERA_XCLK_HZ == 20000000, "The approved OV3660 profile requires 20 MHz XCLK");
static_assert(IP_CAMERA_JPEG_QUALITY >= 0 && IP_CAMERA_JPEG_QUALITY <= 63, "JPEG quality must be 0..63");
static_assert(IP_CAMERA_BRIGHTNESS >= -2 && IP_CAMERA_BRIGHTNESS <= 2, "Brightness must be -2..2");
static_assert(IP_CAMERA_CONTRAST >= -2 && IP_CAMERA_CONTRAST <= 2, "Contrast must be -2..2");
static_assert(IP_CAMERA_SATURATION >= -2 && IP_CAMERA_SATURATION <= 2, "Saturation must be -2..2");
static_assert(IP_CAMERA_SHARPNESS >= -2 && IP_CAMERA_SHARPNESS <= 2, "Sharpness must be -2..2");
static_assert(IP_CAMERA_AE_LEVEL >= -2 && IP_CAMERA_AE_LEVEL <= 2, "AE level must be -2..2");
static_assert(IP_CAMERA_GAIN_CEILING >= -1 && IP_CAMERA_GAIN_CEILING <= 6,
              "Gain ceiling must be -1 (preserve) or 0..6");
static_assert(IP_CAMERA_WARMUP_FRAMES >= 0 && IP_CAMERA_WARMUP_FRAMES <= 10,
              "Warm-up frames must be 0..10");

namespace CameraProfile {
struct Settings {
  const char *name;
  int jpegQuality;
  int brightness;
  int contrast;
  int saturation;
  int sharpness;
  int denoise;
  int aeLevel;
  int gainCeiling;  // -1 preserves the sensor's initialized value.
  unsigned settleMs;
  int warmupFrames;
};

constexpr Settings optimized = {
  "INSPECTPIN_CAMERA_PROFILE_OPTIMIZED",
  IP_CAMERA_JPEG_QUALITY, IP_CAMERA_BRIGHTNESS, IP_CAMERA_CONTRAST,
  IP_CAMERA_SATURATION, IP_CAMERA_SHARPNESS, IP_CAMERA_DENOISE,
  IP_CAMERA_AE_LEVEL, IP_CAMERA_GAIN_CEILING,
  IP_CAMERA_SETTLE_MS, IP_CAMERA_WARMUP_FRAMES
};

// Explicit opt-in experiment; the firmware never selects this automatically.
constexpr Settings lowLightTest = {
  "INSPECTPIN_CAMERA_PROFILE_LOW_LIGHT_TEST",
  IP_CAMERA_JPEG_QUALITY, IP_CAMERA_BRIGHTNESS, IP_CAMERA_CONTRAST,
  IP_CAMERA_SATURATION, IP_CAMERA_SHARPNESS, IP_CAMERA_DENOISE,
  IP_CAMERA_LOW_LIGHT_AE_LEVEL, IP_CAMERA_GAIN_CEILING,
  IP_CAMERA_LOW_LIGHT_SETTLE_MS, IP_CAMERA_LOW_LIGHT_WARMUP_FRAMES
};

constexpr const Settings &selected() {
#if IP_CAMERA_PROFILE == INSPECTPIN_CAMERA_PROFILE_LOW_LIGHT_TEST
  return lowLightTest;
#else
  return optimized;
#endif
}
}
