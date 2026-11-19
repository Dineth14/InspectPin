#include "app_state_machine.h"
#include <esp_task_wdt.h>
App app;
void setup() {
  Serial.begin(115200);
  uint32_t started=millis(); while (!Serial && millis()-started<2000) delay(10);
  // The normal PHOTO/ASK workflows include bounded camera, SD and HTTP calls.
  // Keep the loop task supervised, while allowing those calls to finish.
  Serial.println("BOOT: setup start");
  // Boot performs bounded SD recovery and Wi-Fi association before loop() can
  // feed the task watchdog. Start supervision only after that initialization
  // completes, otherwise a slow hotspot produces a false watchdog reset.
  app.begin();
  esp_task_wdt_config_t watchdogConfig = {
    .timeout_ms = 30000,
    .idle_core_mask = 0,
    .trigger_panic = true,
  };
  enableLoopWDT();
  esp_task_wdt_reconfigure(&watchdogConfig);
}
void loop() { feedLoopWDT(); app.tick(); delay(5); }
