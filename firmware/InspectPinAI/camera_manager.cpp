#include "camera_manager.h"
#include "config.h"
#include "status_feedback.h"
#include <esp_camera.h>
#include <SD.h>
bool captureJpeg(const String &path) {
  if (!IP_CAMERA_ENABLED) { Serial.println("Camera disabled"); return false; }
  camera_config_t c={};
  // Official CAMERA_MODEL_XIAO_ESP32S3 mapping, not AI Thinker ESP32-CAM.
  c.pin_pwdn=-1; c.pin_reset=-1; c.pin_xclk=10;
  c.pin_sccb_sda=40; c.pin_sccb_scl=39;
  c.pin_d0=15; c.pin_d1=17; c.pin_d2=18; c.pin_d3=16;
  c.pin_d4=14; c.pin_d5=12; c.pin_d6=11; c.pin_d7=48;
  c.pin_vsync=38; c.pin_href=47; c.pin_pclk=13;
  c.xclk_freq_hz=20000000; c.ledc_timer=LEDC_TIMER_0; c.ledc_channel=LEDC_CHANNEL_0;
  c.pixel_format=PIXFORMAT_JPEG; c.frame_size=FRAMESIZE_VGA; c.jpeg_quality=12; c.fb_count=1;
  c.fb_location=psramFound()?CAMERA_FB_IN_PSRAM:CAMERA_FB_IN_DRAM;
  if (!psramFound()) c.frame_size=FRAMESIZE_QVGA;
  c.grab_mode=CAMERA_GRAB_WHEN_EMPTY;
  esp_err_t err=esp_camera_init(&c);
  if (err!=ESP_OK) { Serial.printf("Camera init failed: 0x%x\n",err); return false; }
  Feedback::illuminate(true); delay(250);
  // Discard initial frame to let exposure settle.
  camera_fb_t *fb=esp_camera_fb_get(); if (fb) esp_camera_fb_return(fb);
  fb=esp_camera_fb_get(); bool ok=false;
  if (fb && fb->format==PIXFORMAT_JPEG && fb->len>4 && fb->len<=2000000) {
    File f=SD.open(path,FILE_WRITE);
    ok=f && f.write(fb->buf,fb->len)==fb->len; f.flush(); f.close();
    Serial.printf("JPEG saved: %s bytes=%u\n",path.c_str(),unsigned(fb->len));
  }
  if (fb) esp_camera_fb_return(fb);
  Feedback::illuminate(false); esp_camera_deinit(); return ok;
}
