#include "camera_manager.h"
#include "config.h"
#include "camera_profile.h"
#include "status_feedback.h"
#include <SD.h>

namespace {
constexpr size_t kMaximumJpegBytes = 2097152;
constexpr int kCaptureAttempts = 2;

struct ApplyResult {
  unsigned applied = 0;
  unsigned unsupported = 0;
  unsigned failed = 0;
  unsigned mismatched = 0;
};

ApplyResult lastApply;
bool profileApplied = false;
const CameraProfile::Settings *activeProfile = nullptr;

camera_config_t cameraConfiguration() {
  camera_config_t c = {};
  // Official CAMERA_MODEL_XIAO_ESP32S3 mapping, not AI Thinker ESP32-CAM.
  c.pin_pwdn = -1;
  c.pin_reset = -1;
  c.pin_xclk = 10;
  c.pin_sccb_sda = 40;
  c.pin_sccb_scl = 39;
  c.pin_d0 = 15;
  c.pin_d1 = 17;
  c.pin_d2 = 18;
  c.pin_d3 = 16;
  c.pin_d4 = 14;
  c.pin_d5 = 12;
  c.pin_d6 = 11;
  c.pin_d7 = 48;
  c.pin_vsync = 38;
  c.pin_href = 47;
  c.pin_pclk = 13;
  c.xclk_freq_hz = IP_CAMERA_XCLK_HZ;
  c.ledc_timer = LEDC_TIMER_0;
  c.ledc_channel = LEDC_CHANNEL_0;
  c.pixel_format = PIXFORMAT_JPEG;
  c.frame_size = FRAMESIZE_SVGA;
  c.jpeg_quality = CameraProfile::selected().jpegQuality;
  c.fb_count = 1;
  c.fb_location = CAMERA_FB_IN_PSRAM;
  c.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  return c;
}

template <typename T>
bool applyInt(sensor_t *sensor, const char *name,
              int (*setter)(sensor_t *, int), int expected, const T *actual,
              ApplyResult &result, bool required = true) {
  if (!setter) {
    Serial.printf("Camera setting %-18s UNSUPPORTED\n", name);
    ++result.unsupported;
    if (required) ++result.failed;
    return !required;
  }
  int rc = setter(sensor, expected);
  if (rc != 0) {
    Serial.printf("Camera setting %-18s FAILED rc=%d\n", name, rc);
    if (required) ++result.failed;
    else ++result.unsupported;
    return false;
  }
  int readback = int(*actual);
  if (readback != expected) {
    Serial.printf("Camera setting %-18s VERIFY_FAILED expected=%d actual=%d\n",
                  name, expected, readback);
    ++result.mismatched;
    return false;
  }
  Serial.printf("Camera setting %-18s APPLIED value=%d\n", name, readback);
  ++result.applied;
  return true;
}

bool verifyProfile(sensor_t *sensor, const CameraProfile::Settings &p, bool verbose) {
  if (!sensor || sensor->id.PID != OV3660_PID) return false;
  const camera_status_t &s = sensor->status;
  bool ok = sensor->xclk_freq_hz == IP_CAMERA_XCLK_HZ &&
            sensor->pixformat == PIXFORMAT_JPEG &&
            s.framesize == FRAMESIZE_SVGA &&
            s.quality == p.jpegQuality && s.brightness == p.brightness &&
            s.contrast == p.contrast && s.saturation == p.saturation &&
            s.sharpness == p.sharpness && s.denoise == p.denoise &&
            s.ae_level == p.aeLevel && s.awb == 1 && s.awb_gain == 1 &&
            s.wb_mode == 0 && s.aec == 1 && s.aec2 == 0 && s.agc == 1 &&
            s.raw_gma == 1 && (!sensor->set_lenc || s.lenc == 1) &&
            s.dcw == 1 && s.vflip == 1 &&
            s.special_effect == 0;
  if (p.gainCeiling >= 0) ok = ok && s.gainceiling == p.gainCeiling;
  if (verbose && !ok) Serial.println("Camera profile verification FAILED; reapplying settings");
  return ok;
}

bool applyProfile(sensor_t *sensor, const CameraProfile::Settings &p) {
  profileApplied = false;
  activeProfile = &p;
  lastApply = {};
  if (!sensor) {
    Serial.println("Camera profile FAILED: sensor handle unavailable");
    ++lastApply.failed;
    return false;
  }
  if (sensor->id.PID != OV3660_PID) {
    Serial.printf("Camera profile FAILED: expected OV3660 PID=0x%x, detected PID=0x%x\n",
                  OV3660_PID, sensor->id.PID);
    ++lastApply.failed;
    return false;
  }

  int rc = sensor->set_pixformat ? sensor->set_pixformat(sensor, PIXFORMAT_JPEG) : -1;
  if (rc || sensor->pixformat != PIXFORMAT_JPEG) {
    Serial.printf("Camera setting %-18s FAILED rc=%d actual=%d\n", "pixel format", rc,
                  int(sensor->pixformat));
    ++lastApply.failed;
  } else {
    Serial.println("Camera setting pixel format       APPLIED value=JPEG");
    ++lastApply.applied;
  }

  rc = sensor->set_framesize ? sensor->set_framesize(sensor, FRAMESIZE_SVGA) : -1;
  if (rc || sensor->status.framesize != FRAMESIZE_SVGA) {
    Serial.printf("Camera setting %-18s FAILED rc=%d actual=%d\n", "resolution", rc,
                  int(sensor->status.framesize));
    ++lastApply.failed;
  } else {
    Serial.println("Camera setting resolution         APPLIED value=SVGA (800x600)");
    ++lastApply.applied;
  }

  applyInt(sensor, "JPEG quality", sensor->set_quality, p.jpegQuality,
           &sensor->status.quality, lastApply);
  applyInt(sensor, "brightness", sensor->set_brightness, p.brightness,
           &sensor->status.brightness, lastApply);
  applyInt(sensor, "contrast", sensor->set_contrast, p.contrast,
           &sensor->status.contrast, lastApply);
  applyInt(sensor, "saturation", sensor->set_saturation, p.saturation,
           &sensor->status.saturation, lastApply);
  applyInt(sensor, "sharpness", sensor->set_sharpness, p.sharpness,
           &sensor->status.sharpness, lastApply);
  applyInt(sensor, "de-noise", sensor->set_denoise, p.denoise,
           &sensor->status.denoise, lastApply);
  applyInt(sensor, "exposure level", sensor->set_ae_level, p.aeLevel,
           &sensor->status.ae_level, lastApply);
  applyInt(sensor, "AWB", sensor->set_whitebal, 1, &sensor->status.awb, lastApply);
  applyInt(sensor, "AWB gain", sensor->set_awb_gain, 1, &sensor->status.awb_gain, lastApply);
  applyInt(sensor, "AWB mode", sensor->set_wb_mode, 0, &sensor->status.wb_mode, lastApply);
  applyInt(sensor, "AEC", sensor->set_exposure_ctrl, 1, &sensor->status.aec, lastApply);
  applyInt(sensor, "night mode", sensor->set_aec2, 0, &sensor->status.aec2, lastApply);
  applyInt(sensor, "AGC", sensor->set_gain_ctrl, 1, &sensor->status.agc, lastApply);
  applyInt(sensor, "gamma", sensor->set_raw_gma, 1, &sensor->status.raw_gma, lastApply);
  applyInt(sensor, "lens correction", sensor->set_lenc, 1, &sensor->status.lenc, lastApply, false);
  // This is the installed CameraWebServer's mapping for “Advanced AWB”.
  applyInt(sensor, "advanced AWB/DCW", sensor->set_dcw, 1, &sensor->status.dcw, lastApply);
  // Official CameraWebServer correction for the initially inverted OV3660 image.
  applyInt(sensor, "vertical flip", sensor->set_vflip, 1, &sensor->status.vflip, lastApply);
  applyInt(sensor, "special effect", sensor->set_special_effect, 0,
           &sensor->status.special_effect, lastApply);

  if (p.gainCeiling >= 0) {
    if (!sensor->set_gainceiling) {
      Serial.println("Camera setting gain ceiling       UNSUPPORTED");
      ++lastApply.failed;
      ++lastApply.unsupported;
    } else {
      rc = sensor->set_gainceiling(sensor, gainceiling_t(p.gainCeiling));
      if (rc || sensor->status.gainceiling != p.gainCeiling) {
        Serial.printf("Camera setting gain ceiling       FAILED rc=%d actual=%u\n",
                      rc, sensor->status.gainceiling);
        ++lastApply.failed;
      } else {
        Serial.printf("Camera setting gain ceiling       APPLIED value=%d\n", p.gainCeiling);
        ++lastApply.applied;
      }
    }
  } else {
    Serial.printf("Camera setting gain ceiling       PRESERVED initialized value=%u; original tuned value unavailable\n",
                  sensor->status.gainceiling);
  }

  profileApplied = lastApply.failed == 0 && lastApply.mismatched == 0 &&
                   verifyProfile(sensor, p, false);
  return profileApplied;
}

const char *gainCeilingName(uint8_t value) {
  static const char *names[] = {"2x", "4x", "8x", "16x", "32x", "64x", "128x"};
  return value < 7 ? names[value] : "unknown";
}

void shutDownCamera() {
  Feedback::illuminate(false);
  esp_camera_deinit();
  profileApplied = false;
  activeProfile = nullptr;
}

bool initializeCamera() {
  if (!psramFound()) {
    Serial.println("Camera init failed: PSRAM is required for the approved SVGA profile");
    return false;
  }
  camera_config_t c = cameraConfiguration();
  esp_err_t err = esp_camera_init(&c);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed: 0x%x\n", err);
    return false;
  }
  sensor_t *sensor = esp_camera_sensor_get();
  if (!applyConfiguredCameraProfile(sensor)) {
    printCameraSettings();
    shutDownCamera();
    return false;
  }
  printCameraSettings();
  return true;
}

bool warmUpCamera(const CameraProfile::Settings &p) {
  Feedback::illuminate(true);
  delay(p.settleMs);
  for (int i = 0; i < p.warmupFrames; ++i) {
    camera_fb_t *warm = esp_camera_fb_get();
    if (!warm) {
      Serial.printf("Camera warm-up frame %d/%d FAILED\n", i + 1, p.warmupFrames);
      return false;
    }
    esp_camera_fb_return(warm);
    delay(40);
  }
  return true;
}

bool saveJpeg(const String &path, const camera_fb_t *fb) {
  if (SD.exists(path)) {
    Serial.printf("JPEG save refused: destination already exists: %s\n", path.c_str());
    return false;
  }
  File file = SD.open(path, FILE_WRITE);
  if (!file) {
    Serial.printf("JPEG save failed: cannot open %s\n", path.c_str());
    return false;
  }
  size_t written = file.write(fb->buf, fb->len);
  file.flush();
  file.close();
  File check = SD.open(path, FILE_READ);
  bool ok = check && written == fb->len && check.size() == fb->len;
  size_t stored = check ? check.size() : 0;
  check.close();
  if (!ok) {
    Serial.printf("JPEG save verification FAILED expected=%u written=%u stored=%u\n",
                  unsigned(fb->len), unsigned(written), unsigned(stored));
    SD.remove(path);
    return false;
  }
  Serial.printf("JPEG saved and verified: %s bytes=%u resolution=%ux%u\n",
                path.c_str(), unsigned(stored), fb->width, fb->height);
  return true;
}
}

bool applyOptimizedCameraProfile(sensor_t *sensor) {
  return applyProfile(sensor, CameraProfile::optimized);
}

bool applyConfiguredCameraProfile(sensor_t *sensor) {
  return applyProfile(sensor, CameraProfile::selected());
}

bool ensureCameraProfileActive(sensor_t *sensor) {
  const CameraProfile::Settings &selected = CameraProfile::selected();
  if (profileApplied && activeProfile == &selected && verifyProfile(sensor, selected, false)) return true;
  Serial.println("Camera profile is not active; applying it before capture");
  return applyConfiguredCameraProfile(sensor);
}

void printCameraSettings() {
  sensor_t *sensor = esp_camera_sensor_get();
  Serial.println("===================================");
  Serial.println(" InspectPin OV3660 Camera Profile");
  Serial.println("===================================");
  if (!sensor) {
    Serial.println("Camera detected: unavailable");
    Serial.println("Optimized profile: FAILED");
    Serial.println("===================================");
    return;
  }
  const camera_status_t &s = sensor->status;
  Serial.printf("Profile: %s\n", activeProfile ? activeProfile->name : "none");
  Serial.printf("Camera detected: %s (PID 0x%x)\n", sensor->id.PID == OV3660_PID ? "OV3660" : "OTHER", sensor->id.PID);
  Serial.printf("XCLK: %d MHz\n", sensor->xclk_freq_hz / 1000000);
  Serial.printf("Resolution: %s\n", s.framesize == FRAMESIZE_SVGA ? "SVGA (800x600)" : "UNEXPECTED");
  Serial.printf("Pixel format: %s\n", sensor->pixformat == PIXFORMAT_JPEG ? "JPEG" : "UNEXPECTED");
  Serial.printf("JPEG quality: %u\n", s.quality);
  Serial.printf("Brightness: %d\nContrast: %d\nSaturation: %d\n", s.brightness, s.contrast, s.saturation);
  Serial.printf("Sharpness: %d\nDe-noise: %u\nExposure level: %d\n", s.sharpness, s.denoise, s.ae_level);
  if (activeProfile && activeProfile->gainCeiling < 0)
    Serial.printf("Gain ceiling status: %u [raw initialized driver value preserved; tuned reference unavailable]\n",
                  s.gainceiling);
  else
    Serial.printf("Gain ceiling: %u (%s)\n", s.gainceiling, gainCeilingName(s.gainceiling));
  Serial.printf("AWB: %s\nAWB gain: %s\nAWB mode: %u (0=auto)\n",
                s.awb ? "Enabled" : "Disabled", s.awb_gain ? "Enabled" : "Disabled", s.wb_mode);
  Serial.printf("Advanced AWB/DCW: %s\nAEC: %s\nAGC: %s\nGMA: %s\nLens correction: %s\n",
                s.dcw ? "Enabled" : "Disabled", s.aec ? "Enabled" : "Disabled",
                s.agc ? "Enabled" : "Disabled", s.raw_gma ? "Enabled" : "Disabled",
                s.lenc ? "Enabled" : "Disabled");
  Serial.printf("Night mode (AEC2): %s\nVertical flip: %s\n",
                s.aec2 ? "Enabled" : "Disabled", s.vflip ? "Enabled" : "Disabled");
  Serial.printf("Setter results: applied=%u unsupported=%u failed=%u verify_mismatch=%u\n",
                lastApply.applied, lastApply.unsupported, lastApply.failed, lastApply.mismatched);
  Serial.printf("Optimized profile: %s\n", profileApplied
                ? (activeProfile && activeProfile->gainCeiling < 0
                   ? "APPLIED AND VERIFIED; GAIN CEILING PRESERVED, TUNED REFERENCE UNVERIFIED"
                   : "APPLIED AND VERIFIED")
                : "FAILED OR UNVERIFIED");
  Serial.println("===================================");
}

bool captureJpeg(const String &path) {
  if (!IP_CAMERA_ENABLED) {
    Serial.println("Camera disabled");
    return false;
  }
  for (int attempt = 1; attempt <= kCaptureAttempts; ++attempt) {
    Serial.printf("Camera capture attempt %d/%d\n", attempt, kCaptureAttempts);
    if (!initializeCamera()) continue;
    sensor_t *sensor = esp_camera_sensor_get();
    if (!ensureCameraProfileActive(sensor) || !warmUpCamera(CameraProfile::selected())) {
      shutDownCamera();
      continue;
    }

    camera_fb_t *fb = esp_camera_fb_get();
    bool valid = fb && fb->format == PIXFORMAT_JPEG && fb->len > 4 &&
                 fb->len <= kMaximumJpegBytes && fb->width == 800 && fb->height == 600 &&
                 fb->buf[0] == 0xff && fb->buf[1] == 0xd8 &&
                 fb->buf[fb->len - 2] == 0xff && fb->buf[fb->len - 1] == 0xd9;
    if (!valid) {
      Serial.printf("JPEG capture validation FAILED fb=%s format=%d bytes=%u resolution=%ux%u\n",
                    fb ? "present" : "null", fb ? int(fb->format) : -1,
                    fb ? unsigned(fb->len) : 0, fb ? fb->width : 0, fb ? fb->height : 0);
      if (fb) esp_camera_fb_return(fb);
      shutDownCamera();
      continue;
    }

    bool ok = saveJpeg(path, fb);
    esp_camera_fb_return(fb);
    shutDownCamera();
    return ok;
  }
  Serial.println("Camera capture FAILED after reinitialization retry");
  return false;
}

bool diagnoseCamera() {
  if (!IP_CAMERA_ENABLED) {
    Serial.println("Camera disabled");
    return false;
  }
  bool ok = initializeCamera();
  if (ok) shutDownCamera();
  return ok;
}
