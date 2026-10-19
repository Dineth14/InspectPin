#include "sd_manager.h"
#include "config.h"
#include <SD.h>
#include <SPI.h>
#include <esp_system.h>
#include <ArduinoJson.h>
namespace {
bool validId(const String &value) {
  if (!value.length()) return true;
  if (value.length()!=32) return false;
  for (char c:value) if (!isxdigit(c)) return false;
  return true;
}
}
bool Store::begin() {
  SPI.begin(Config::sdSCK,Config::sdMISO,Config::sdMOSI,Config::sdCS);
  if (!SD.begin(Config::sdCS) || SD.cardType()==CARD_NONE) return false;
  if (!SD.exists("/inspectpin") && !SD.mkdir("/inspectpin")) return false;
  Serial.printf("SD card initialized: %llu MB\n",SD.cardSize()/1024/1024);
  return true;
}
String Store::newPath(bool image) {
  char path[80];
  do { snprintf(path,sizeof(path),"/inspectpin/%08lx_%08lx.%s",(unsigned long)esp_random(),(unsigned long)millis(), image?"jpg":"wav"); }
  while (SD.exists(path));
  return String(path);
}
bool Store::markPending(const String &path, const String &job, const String &imageId, const String &contextId) {
  // Save the original association: retry must never silently use a newer image.
  String temporary=path+".pending.tmp", finalPath=path+".pending";
  File f=SD.open(temporary,FILE_WRITE);
  if (!f) return false;
  JsonDocument doc; doc["version"]=2; doc["job"]=job; doc["image_id"]=imageId; doc["context_id"]=contextId;
  bool ok=serializeJson(doc,f)==measureJson(doc); f.flush(); f.close();
  if (!ok) return false;
  if (SD.exists(finalPath) && !SD.remove(finalPath)) return false;
  return SD.rename(temporary,finalPath);
}
bool Store::nextPending(String &path, String &job, String &imageId, String &contextId) {
  File dir=SD.open("/inspectpin");
  if (!dir) return false;
  for (File entry=dir.openNextFile(); entry; entry=dir.openNextFile()) {
    String name=entry.name();
    if (!entry.isDirectory() && name.endsWith(".pending")) {
      path=String("/inspectpin/")+name.substring(0,name.length()-8);
      job=""; imageId=""; contextId="";
      if (entry.peek()=='{') {
        JsonDocument doc;
        if (entry.size()>1024 || deserializeJson(doc,entry) || doc["version"]!=2 ||
            !doc["job"].is<const char*>() || !doc["image_id"].is<const char*>() || !doc["context_id"].is<const char*>()) {
          Serial.println("Skipping corrupt pending metadata; original input retained"); entry.close(); continue;
        }
        job=doc["job"] | ""; imageId=doc["image_id"] | ""; contextId=doc["context_id"] | "";
      } else { job=entry.readStringUntil('\n'); job.trim(); }  // Original voice-only journals.
      entry.close();
      if (!SD.exists(path)) continue;
      if (!validId(job) || !validId(imageId) || !validId(contextId)) {
        Serial.println("Skipping invalid pending IDs; refusing to change image association"); continue;
      }
      dir.close();
      return true;
    }
    entry.close();
  }
  dir.close(); return false;
}
void Store::complete(const String &path) { SD.remove(path+".pending"); }
bool Store::selfTest() {
  const char *path="/inspectpin/sd-selftest.tmp";
  File f=SD.open(path,FILE_WRITE);
  if (!f) return false;
  bool ok=f.print("InspectPin SD test\n")==19; f.close();
  f=SD.open(path,FILE_READ); ok=ok && f && f.readString()=="InspectPin SD test\n";
  f.close(); return SD.remove(path) && ok;
}
