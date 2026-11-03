#include "video_recorder.h"
#include "video_profile.h"
#include "avi_writer.h"
#include "camera_manager.h"
#include <SD.h>
namespace {AviWriter writer;Video::Stats current;String finalPath,partialPath;uint32_t nextFrame=0;}
bool Video::begin(const String &path){
  if(current.active)return false;finalPath=path;partialPath=path+".part";current={};current.path=path;
  if(SD.totalBytes()-SD.usedBytes()<VideoProfile::minimumFreeBytes){current.error="VIDEO_STORAGE_LOW";return false;}
  if(!beginVideoCamera()){current.error="VIDEO_CAMERA_INIT_FAILED";return false;}
  if(!writer.begin(partialPath,VideoProfile::width,VideoProfile::height,VideoProfile::targetFps)){current.error=writer.error();endVideoCamera();return false;}
  current.active=true;current.startedAt=millis();nextFrame=current.startedAt;Serial.printf("Video started: %s profile=%s %ux%u @ target %u fps\n",path.c_str(),VideoProfile::name,VideoProfile::width,VideoProfile::height,VideoProfile::targetFps);return true;
}
void Video::tick(bool criticalBattery){
  if(!current.active)return;
  if(criticalBattery){current.error="CRITICAL_BATTERY";stop("critical battery");return;}
  if(millis()-current.startedAt>=VideoProfile::maximumDurationMs){stop("duration limit");return;}
  if(SD.totalBytes()-SD.usedBytes()<VideoProfile::minimumFreeBytes){current.error="VIDEO_STORAGE_LOW";stop("storage limit");return;}
  uint32_t now=millis();current.elapsedMs=now-current.startedAt;
  if(int32_t(now-nextFrame)<0)return;const uint32_t period=1000U/VideoProfile::targetFps;
  if(now-nextFrame>=period){current.dropped+=(now-nextFrame)/period;nextFrame=now;}nextFrame+=period;
  camera_fb_t *frame=getVideoFrame();if(!frame){current.dropped++;return;}
  bool valid=frame->format==PIXFORMAT_JPEG&&frame->width==VideoProfile::width&&frame->height==VideoProfile::height;
  if(!valid||!writer.appendJpeg(frame->buf,frame->len)){current.error=valid?writer.error():"VIDEO_FRAME_INVALID";returnVideoFrame(frame);stop(current.error.c_str());return;}
  returnVideoFrame(frame);current.frames=writer.frameCount();current.bytes=writer.bytesWritten();
}
bool Video::stop(const char *reason){
  if(!current.active)return false;current.active=false;bool ok=writer.finalize();endVideoCamera();
  if(ok){if(SD.exists(finalPath))SD.remove(finalPath);ok=SD.rename(partialPath,finalPath);}if(!ok&&current.error.isEmpty())current.error=writer.error().length()?writer.error():"VIDEO_FINALIZE_FAILED";
  current.frames=writer.frameCount();current.bytes=writer.bytesWritten();current.elapsedMs=millis()-current.startedAt;
  Serial.printf("Video stopped: reason=%s ok=%s frames=%lu dropped=%lu bytes=%lu elapsed_ms=%lu path=%s error=%s\n",reason?reason:"unknown",ok?"yes":"no",(unsigned long)current.frames,(unsigned long)current.dropped,(unsigned long)current.bytes,(unsigned long)current.elapsedMs,finalPath.c_str(),current.error.c_str());return ok;
}
bool Video::active(){return current.active;}Video::Stats Video::stats(){return current;}
void Video::recoverIncomplete(){
  File dir=SD.open("/inspectpin");if(!dir)return;for(File entry=dir.openNextFile();entry;entry=dir.openNextFile()){String name=entry.name();entry.close();if(name.endsWith(".avi.part")){String from=String("/inspectpin/")+name,to=from+".incomplete";if(!SD.exists(to)&&SD.rename(from,to))Serial.printf("Recovered incomplete video marker: %s\n",to.c_str());}}
  dir.close();
}

