#pragma once
#include <Arduino.h>
#include <SD.h>
class AviWriter {
 public:
  bool begin(const String &partialPath,uint16_t width,uint16_t height,uint8_t fps);
  bool appendJpeg(const uint8_t *data,size_t length);
  bool finalize();
  void abort();
  uint32_t frameCount() const{return frames_;}
  uint32_t bytesWritten() const{return bytes_;}
  const String &error() const{return error_;}
 private:
  File avi_,index_;
  String partial_,indexPath_,error_;
  uint16_t width_=0,height_=0;uint8_t fps_=0;
  uint32_t frames_=0,bytes_=0,moviTypeOffset_=0,moviSizeOffset_=0;
  uint32_t riffSizeOffset_=0,totalFramesOffset_=0,streamLengthOffset_=0;
  bool writeFourCC(const char value[4]);
  bool writeU16(uint16_t value);bool writeU32(uint32_t value);bool patchU32(uint32_t offset,uint32_t value);
};

