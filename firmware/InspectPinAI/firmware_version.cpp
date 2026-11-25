#include "firmware_version.h"
#include "config.h"
#include <esp_ota_ops.h>

#ifndef IP_FIRMWARE_VERSION
#define IP_FIRMWARE_VERSION "1.1.0"
#endif
#ifndef IP_FIRMWARE_BUILD_ID
#define IP_FIRMWARE_BUILD_ID __DATE__ " " __TIME__
#endif

const char *FirmwareVersion::version() { return IP_FIRMWARE_VERSION; }
const char *FirmwareVersion::build() { return IP_FIRMWARE_BUILD_ID; }
const char *FirmwareVersion::hardware() {
#if defined(IP_USE_SINGLE_LAYER_CONFIG)
  return "xiao-esp32s3-sense-single-layer";
#else
  return "inspectpin-other";
#endif
}
void FirmwareVersion::write(JsonObject out) {
  out["version"]=version();
  out["build"]=build();
  out["built_at"]=__DATE__ " " __TIME__;
  out["hardware"]=hardware();
  const auto *running=esp_ota_get_running_partition();
  const auto *available=esp_ota_get_next_update_partition(nullptr);
  if (running) out["boot_slot"]=running->label;
  static const String imageDigest=[running]() {
    uint8_t digest[32];
    if (!running || esp_partition_get_sha256(running,digest)!=ESP_OK) return String();
    char hex[65];
    for (size_t i=0;i<sizeof(digest);++i) snprintf(hex+2*i,3,"%02x",unsigned(digest[i]));
    return String(hex);
  }();
  if (imageDigest.length()) out["image_sha256"]=imageDigest;
  out["inactive_slot_bytes"]=available?available->size:0;
  out["ota_enabled"]=false;
}
