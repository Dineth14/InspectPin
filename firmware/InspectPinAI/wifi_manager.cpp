#include "wifi_manager.h"
#include "config.h"
#include <WiFi.h>
bool Wifi::connect() {
  if (WiFi.status()==WL_CONNECTED) return true;
  // A timed-out ESP32 association can remain in WL_IDLE_STATUS/connecting.
  // Starting another scan or begin() in that state produces
  // "sta is connecting, cannot set config" and prevents recovery.
  WiFi.mode(WIFI_STA);
  WiFi.disconnect(false,false);
  delay(100);
  WiFi.begin(IP_WIFI_SSID,IP_WIFI_PASSWORD);
  uint32_t start=millis();
  while (WiFi.status()!=WL_CONNECTED && millis()-start<Config::wifiTimeoutMs) delay(100);
  if (WiFi.status()!=WL_CONNECTED) {
    WiFi.disconnect(false,false);
    Serial.println("Wi-Fi unavailable; SD input retained");
    return false;
  }
  Serial.printf("Wi-Fi connected IP=%s RSSI=%d\n",WiFi.localIP().toString().c_str(),WiFi.RSSI()); return true;
}
void Wifi::scan() {
  WiFi.mode(WIFI_STA);
  if(WiFi.status()!=WL_CONNECTED){WiFi.disconnect(false,false);delay(100);}
  int count=WiFi.scanNetworks();
  Serial.printf("Networks found: %d\n",count);
  for (int i=0;i<count;i++) Serial.printf("%s RSSI=%d channel=%d\n",WiFi.SSID(i).c_str(),WiFi.RSSI(i),WiFi.channel(i));
  WiFi.scanDelete();
}
