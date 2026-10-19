#include "app_state_machine.h"
App app;
void setup() {
  Serial.begin(115200);
  uint32_t started=millis(); while (!Serial && millis()-started<2000) delay(10);
  app.begin();
}
void loop() { app.tick(); delay(5); }
