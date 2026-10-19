#include "sd_manager.h"
#include "config.h"
#include <SD.h>
#include <SPI.h>
#include <esp_system.h>
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
bool Store::markPending(const String &path, const String &job) {
  // Short journal; a torn write can lose a job ID, but never the captured input.
  File f=SD.open(path+".pending",FILE_WRITE);
  if (!f) return false;
  String value=job+"\n";
  bool ok=f.print(value)==value.length(); f.flush(); f.close(); return ok;
}
bool Store::nextPending(String &path, String &job) {
  File dir=SD.open("/inspectpin");
  if (!dir) return false;
  for (File entry=dir.openNextFile(); entry; entry=dir.openNextFile()) {
    String name=entry.name();
    if (!entry.isDirectory() && name.endsWith(".pending")) {
      path=String("/inspectpin/")+name.substring(0,name.length()-8);
      job=entry.readStringUntil('\n'); job.trim(); entry.close(); dir.close();
      if (job.length()!=32) job="";
      for (char c:job) { if (!isxdigit(c)) { job=""; break; } }
      return SD.exists(path);
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
