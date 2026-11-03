#include "power_manager.h"
#include "config.h"
#include <WiFi.h>
#include <esp_sleep.h>
#include <driver/rtc_io.h>
#include "hardware_profile.h"
#include "pcf8574_manager.h"

namespace { uint32_t lastActivity=0,idleTimeout=IP_IDLE_TIMEOUT_MS; const char *cause="power-on/reset"; }

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
void Power::setIdleTimeout(uint32_t timeoutMs){idleTimeout=timeoutMs;noteActivity();}
bool Power::idleExpired() { return IP_POWER_MANAGEMENT_ENABLED && idleTimeout>0 && millis()-lastActivity>=idleTimeout; }
const char *Power::wakeCause() { return cause; }
bool Power::enterLightSleep() {
  if (!IP_POWER_MANAGEMENT_ENABLED) return false;
  if(digitalRead(HardwareProfile::askButtonGpio)==LOW)return false;
  gpio_wakeup_enable(gpio_num_t(HardwareProfile::askButtonGpio),GPIO_INTR_LOW_LEVEL);
  if(IP_PCF8574_ENABLED){if(!Expander::prepareForSleep()||digitalRead(HardwareProfile::pcfInterruptGpio)==LOW)return false;gpio_wakeup_enable(gpio_num_t(HardwareProfile::pcfInterruptGpio),GPIO_INTR_LOW_LEVEL);}
  esp_sleep_enable_gpio_wakeup();
  Serial.println("Entering light sleep"); Serial.flush();
  esp_light_sleep_start();
  gpio_wakeup_disable(gpio_num_t(HardwareProfile::askButtonGpio));
  if(IP_PCF8574_ENABLED)gpio_wakeup_disable(gpio_num_t(HardwareProfile::pcfInterruptGpio));noteActivity();
  Serial.println("Returned from light sleep"); return true;
}
bool Power::enterDeepSleep(const char *reason) {
  if (!IP_POWER_MANAGEMENT_ENABLED) { Serial.println("Deep sleep disabled until wake hardware is validated"); return false; }
  WiFi.disconnect(true); WiFi.mode(WIFI_OFF);
  if(digitalRead(HardwareProfile::askButtonGpio)==LOW)return false;
  uint64_t wakeMask=1ULL<<HardwareProfile::askButtonGpio;
  if(IP_PCF8574_ENABLED){if(!Expander::prepareForSleep()||digitalRead(HardwareProfile::pcfInterruptGpio)==LOW)return false;wakeMask|=1ULL<<HardwareProfile::pcfInterruptGpio;}
  esp_sleep_enable_ext1_wakeup_io(wakeMask,ESP_EXT1_WAKEUP_ANY_LOW);
  Serial.printf("Entering deep sleep: %s\n",reason?reason:"requested"); Serial.flush();
  esp_deep_sleep_start(); return true;
}
bool Power::enterAutomaticSleep(const char *reason){
  if(!IP_POWER_MANAGEMENT_ENABLED){Serial.println("Automatic sleep disabled until wake hardware is validated");return false;}
  if(IP_DEEP_SLEEP_ENABLED)return enterDeepSleep(reason);
  Serial.printf("Automatic policy selecting light sleep: %s\n",reason?reason:"idle");
  return enterLightSleep();
}
