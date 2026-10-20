#pragma once
#include <Arduino.h>
#include <esp_camera.h>

bool applyOptimizedCameraProfile(sensor_t *sensor);
bool applyConfiguredCameraProfile(sensor_t *sensor);
bool ensureCameraProfileActive(sensor_t *sensor);
void printCameraSettings();
bool diagnoseCamera();
bool captureJpeg(const String &path);
