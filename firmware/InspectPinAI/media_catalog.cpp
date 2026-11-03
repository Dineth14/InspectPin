#include "media_catalog.h"
#include <SD.h>
void MediaCatalog::print(){File dir=SD.open("/inspectpin");if(!dir){Serial.println("Media catalogue unavailable");return;}unsigned count=0;for(File entry=dir.openNextFile();entry;entry=dir.openNextFile()){String name=entry.name();if(!entry.isDirectory()&&(name.endsWith(".jpg")||name.endsWith(".wav")||name.endsWith(".avi")||name.endsWith(".incomplete"))){Serial.printf("MEDIA name=%s bytes=%lu\n",name.c_str(),(unsigned long)entry.size());count++;}entry.close();}dir.close();Serial.printf("Media count=%u free_bytes=%llu\n",count,SD.totalBytes()-SD.usedBytes());}
bool MediaCatalog::sendFile(const String &path){
  String selected=path;
  if(!selected.endsWith(".avi")){
    File dir=SD.open("/inspectpin");for(File entry=dir.openNextFile();entry;entry=dir.openNextFile()){String name=entry.name();if(!entry.isDirectory()&&name.endsWith(".avi"))selected=String("/inspectpin/")+name;entry.close();}dir.close();
  }
  if(!selected.endsWith(".avi")){Serial.println("MEDIA_DOWNLOAD_FAILED no finalized video selected");return false;}
  File file=SD.open(selected,FILE_READ);if(!file){Serial.println("MEDIA_DOWNLOAD_FAILED open");return false;}
  Serial.printf("MEDIA_BINARY_BEGIN size=%lu path=%s\n",(unsigned long)file.size(),selected.c_str());Serial.flush();
  uint8_t buffer[1024];while(file.available()){size_t got=file.read(buffer,sizeof(buffer));if(Serial.write(buffer,got)!=got){file.close();return false;}}file.close();Serial.flush();return true;
}
