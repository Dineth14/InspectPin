#pragma once
#include <esp_camera.h>
namespace VideoProfile {
constexpr framesize_t frameSize=FRAMESIZE_QVGA;
constexpr uint16_t width=320,height=240;
constexpr uint8_t jpegQuality=15;
constexpr uint8_t targetFps=5;
constexpr uint32_t maximumDurationMs=30000;
constexpr uint32_t minimumFreeBytes=8UL*1024UL*1024UL;
constexpr const char *name="INSPECTPIN_VIDEO_PROFILE_QVGA_BENCH";
}

