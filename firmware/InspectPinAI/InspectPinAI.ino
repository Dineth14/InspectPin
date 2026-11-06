#include "app_state_machine.h"
#include <esp_task_wdt.h>
App app;
void setup() {
  Serial.begin(115200);
  uint32_t started=millis(); while (!Serial && millis()-started<2000) delay(10);
  // The normal PHOTO/ASK workflows include bounded camera, SD and HTTP calls.
  // Keep the loop task supervised, while allowing those calls to finish.
  enableLoopWDT();
  esp_task_wdt_config_t watchdogConfig = {
    .timeout_ms = 30000,
    .idle_core_mask = 0,
    .trigger_panic = true,
  };
  esp_task_wdt_reconfigure(&watchdogConfig);
  app.begin();
}
void loop() { feedLoopWDT(); app.tick(); delay(5); }
