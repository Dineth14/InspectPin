#include "network_profile.h"
#include "config.h"
#include "api_client.h"
#include "wifi_manager.h"
#include <ArduinoJson.h>
#include <Preferences.h>
#include <WiFi.h>

namespace {
using NetworkProfile::Profile;
Profile profile;
bool validOrigin(const String &origin) {
  bool tls=origin.startsWith("https://");
  if (!tls && !origin.startsWith("http://")) return false;
  String host=origin.substring(tls?8:7);
  int colon=host.indexOf(':');
  if (colon>=0) {
    String port=host.substring(colon+1);
    if (!port.length() || port.length()>5 || port.toInt()<1 || port.toInt()>65535) return false;
    for (char c:port) if (!isdigit(c)) return false;
    host.remove(colon);
  }
  if (!host.length() || host.length()>253) return false;
  for (char c:host) if (!isalnum(c) && c!='-' && c!='.') return false;
  if (tls) return strlen(IP_SERVER_CA_CERT)>100;
  IPAddress ip;
  return ip.fromString(host) && (ip[0]==10 || (ip[0]==192 && ip[1]==168) ||
    (ip[0]==172 && ip[1]>=16 && ip[1]<=31));
}
bool decode(const String &line, Profile &p) {
  JsonDocument doc;
  if (deserializeJson(doc,line)) return false;
  for (auto field:{"ssid","password","origin","token"}) if (!doc[field].is<const char*>()) return false;
  p={doc["ssid"].as<String>(),doc["password"].as<String>(),doc["origin"].as<String>(),doc["token"].as<String>()};
  if (!p.token.length() && p.origin==profile.origin) p.token=profile.token;
  if (!p.ssid.length() || p.ssid.length()>32 || p.password.length()>64 || !validOrigin(p.origin) ||
      p.token.length()<16 || p.token.length()>512) return false;
  for(char c:p.token) if(c<=32 || c>=127) return false;
  return true;
}
}
const NetworkProfile::Profile &NetworkProfile::active(){ return profile; }
void NetworkProfile::load(){
  profile={IP_WIFI_SSID,IP_WIFI_PASSWORD,IP_SERVER_URL,IP_DEVICE_TOKEN};
  Preferences nvs;
  if(nvs.begin("ip-network",true)){
    Profile saved;
    if(decode(nvs.getString("profile",""),saved)) profile=saved;
    nvs.end();
  }
}
void NetworkProfile::configureUsb(){
  Serial.println("IP_SETUP_READY");
  String line;
  uint32_t start=millis();
  bool complete=false;
  while(millis()-start<5000){
    if (!Serial.available()){delay(1);continue;}
    int c=Serial.read();
    if(c=='\n'){complete=true;break;}
    if(line.length()<1537 && c!='\r') line+=char(c);
  }
  Profile candidate;
  if(!complete || line.length()>1536 || !decode(line,candidate)){Serial.println("IP_SETUP_INVALID");return;}
  Profile previous=profile;
  profile=candidate;
  WiFi.disconnect(false,false);
  delay(150);
  String error;
  SessionContext session;
  Preferences nvs;
  bool saved=false;
  if(Wifi::connect() && Api::session(session,error) && Api::heartbeat("READY",error) && nvs.begin("ip-network",false)){
    JsonDocument persistent;
    persistent["ssid"]=candidate.ssid; persistent["password"]=candidate.password;
    persistent["origin"]=candidate.origin; persistent["token"]=candidate.token;
    String record;serializeJson(persistent,record);
    saved=nvs.putString("profile",record)==record.length();
    nvs.end();
  }
  if(!saved){profile=previous;WiFi.disconnect(false,false);}
  Serial.println(saved?"IP_SETUP_SAVED":"IP_SETUP_REJECTED");
  Serial.flush();
  ESP.restart();
}
