#include "power_manager.h"
#include "config.h"
#include <WiFi.h>
#include <esp_sleep.h>
#include <driver/rtc_io.h>

namespace { uint32_t lastActivity=0; const char *cause="power-on/reset"; }

void Power::begin() {
  lastActivity=millis();
  switch (esp_sleep_get_wakeup_cause()) {
    case ESP_SLEEP_WAKEUP_EXT1: cause="external button"; break;
    case ESP_SLEEP_WAKEUP_TIMER: cause="timer"; break;
    case ESP_SLEEP_WAKEUP_GPIO: cause="gpio"; break;
    default: cause="power-on/reset"; break;
  }
  Serial.printf("Wake cause: %s\n",cause);
}
void Power::noteActivity() { lastActivity=millis(); }
bool Power::idleExpired() { return IP_POWER_MANAGEMENT_ENABLED && IP_IDLE_TIMEOUT_MS>0 && millis()-lastActivity>=IP_IDLE_TIMEOUT_MS; }
const char *Power::wakeCause() { return cause; }
bool Power::enterLightSleep() {
  if (!IP_POWER_MANAGEMENT_ENABLED) return false;
  gpio_wakeup_enable(gpio_num_t(IP_POWER_BUTTON_PIN),GPIO_INTR_LOW_LEVEL);
  esp_sleep_enable_gpio_wakeup();
  Serial.println("Entering light sleep"); Serial.flush();
  esp_light_sleep_start();
  gpio_wakeup_disable(gpio_num_t(IP_POWER_BUTTON_PIN)); noteActivity();
  Serial.println("Returned from light sleep"); return true;
}
bool Power::enterDeepSleep(const char *reason) {
  if (!IP_POWER_MANAGEMENT_ENABLED) { Serial.println("Deep sleep disabled until wake hardware is validated"); return false; }
  WiFi.disconnect(true); WiFi.mode(WIFI_OFF);
  pinMode(IP_POWER_BUTTON_PIN,INPUT_PULLUP);
  esp_sleep_enable_ext1_wakeup_io(1ULL<<IP_POWER_BUTTON_PIN,ESP_EXT1_WAKEUP_ANY_LOW);
  Serial.printf("Entering deep sleep: %s\n",reason?reason:"requested"); Serial.flush();
  esp_deep_sleep_start(); return true;
}
