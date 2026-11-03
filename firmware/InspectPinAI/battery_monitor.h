#pragma once
#include <Arduino.h>
namespace Battery {
struct Reading {
  float volts=-1, percent=-1, uncertaintyVolts=0.08f;
  bool valid=false, low=false, critical=false;
  uint32_t sampledAt=0;
};
void begin();
Reading sample();
Reading latest();
float volts();
bool low();
bool critical();
}
