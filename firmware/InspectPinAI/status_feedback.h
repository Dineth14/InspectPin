#pragma once
#include <Arduino.h>
namespace Feedback {
enum class Event : uint8_t { WAKE, READY, RECORDING_STARTED, RECORDING_STOPPED, CAPTURE_OK, VIDEO_STARTED, VIDEO_STOPPED, ANSWER_READY, WIFI_LOST, LOW_BATTERY, ERROR };
void begin();
void tick();
void signal(Event event);
void pulse();
void illuminate(bool enabled);
void setLight(bool enabled,uint8_t brightness=255,uint32_t timeoutMs=0);
bool lightOn();
uint8_t lightBrightness();
}
