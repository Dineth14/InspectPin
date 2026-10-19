#include "status_feedback.h"
#include "config.h"
void Feedback::begin() {
  if (IP_LIGHT_ENABLED) { pinMode(Config::light,OUTPUT); digitalWrite(Config::light,LOW); }
  if (IP_HAPTIC_ENABLED) { pinMode(Config::haptic,OUTPUT); digitalWrite(Config::haptic,LOW); }
}
void Feedback::pulse() {
  // Bounded pulse, including when the next action blocks on audio or networking.
  if (IP_HAPTIC_ENABLED) { digitalWrite(Config::haptic,HIGH); delay(60); digitalWrite(Config::haptic,LOW); }
}
void Feedback::illuminate(bool enabled) { if (IP_LIGHT_ENABLED) digitalWrite(Config::light,enabled?HIGH:LOW); }
