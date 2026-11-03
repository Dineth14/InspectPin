#pragma once
#include <stddef.h>
#include <stdint.h>

namespace BatteryPolicy {
struct CurvePoint { float volts; float percent; };

constexpr CurvePoint curve[] = {
  {3.20f,0.0f},{3.35f,5.0f},{3.50f,12.0f},{3.60f,25.0f},{3.70f,50.0f},
  {3.80f,70.0f},{3.90f,85.0f},{4.00f,94.0f},{4.10f,98.0f},{4.20f,100.0f}
};

inline float percentFromVoltage(float voltage) {
  if (voltage <= curve[0].volts) return 0.0f;
  constexpr size_t count = sizeof(curve)/sizeof(curve[0]);
  if (voltage >= curve[count-1].volts) return 100.0f;
  for (size_t i=1;i<count;i++) if (voltage<=curve[i].volts) {
    const CurvePoint &a=curve[i-1], &b=curve[i];
    return a.percent+(voltage-a.volts)*(b.percent-a.percent)/(b.volts-a.volts);
  }
  return -1.0f;
}

inline bool updateLowLatch(bool latched,float voltage,float threshold,float hysteresis) {
  return latched ? voltage < threshold+hysteresis : voltage < threshold;
}

inline float trimmedMean(const uint16_t *sorted,size_t count,size_t trim) {
  if (!sorted || count==0 || trim*2>=count) return -1.0f;
  uint32_t sum=0;
  for(size_t i=trim;i<count-trim;i++) sum+=sorted[i];
  return static_cast<float>(sum)/static_cast<float>(count-trim*2);
}
}

