#pragma once
#include <Arduino.h>

namespace Ina219 {
struct Reading {
  float busVolts = 0;
  float shuntMillivolts = 0;
  float packVolts = 0;
  float currentMilliamps = 0;
  float powerMilliwatts = 0;
  bool valid = false;
  uint32_t sampledAt = 0;
};
bool begin();
Reading sample();
Reading latest();
bool available();
uint16_t calibrationRegister();
}
