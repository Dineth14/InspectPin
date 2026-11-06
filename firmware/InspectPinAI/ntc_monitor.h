#pragma once
#include <Arduino.h>
namespace Ntc {
struct Reading { float adcVolts=0,resistanceOhms=0,celsius=0;bool valid=false,safe=false,openCircuit=false,shortCircuit=false;uint32_t sampledAt=0; };
void begin();
Reading sample();
Reading latest();
}
