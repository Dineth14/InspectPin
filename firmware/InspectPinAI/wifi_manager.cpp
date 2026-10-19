#include "wifi_manager.h"
#include "config.h"
#include <WiFi.h>
bool Wifi::connect() {
  if (WiFi.status()==WL_CONNECTED) return true;
  WiFi.mode(WIFI_STA); WiFi.begin(IP_WIFI_SSID,IP_WIFI_PASSWORD);
  uint32_t start=millis();
  while (WiFi.status()!=WL_CONNECTED && millis()-start<Config::wifiTimeoutMs) delay(100);
  if (WiFi.status()!=WL_CONNECTED) { Serial.println("Wi-Fi unavailable; SD input retained"); return false; }
  Serial.printf("Wi-Fi connected IP=%s RSSI=%d\n",WiFi.localIP().toString().c_str(),WiFi.RSSI()); return true;
}
void Wifi::scan() {
  WiFi.mode(WIFI_STA); int count=WiFi.scanNetworks();
  Serial.printf("Networks found: %d\n",count);
  for (int i=0;i<count;i++) Serial.printf("%s RSSI=%d channel=%d\n",WiFi.SSID(i).c_str(),WiFi.RSSI(i),WiFi.channel(i));
  WiFi.scanDelete();
}
