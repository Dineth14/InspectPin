#include "avi_writer.h"
namespace {
bool writeBytes(File &file,const void *data,size_t length){return file.write(static_cast<const uint8_t*>(data),length)==length;}
}
bool AviWriter::writeFourCC(const char value[4]){return writeBytes(avi_,value,4);}
bool AviWriter::writeU16(uint16_t v){uint8_t b[2]={uint8_t(v),uint8_t(v>>8)};return writeBytes(avi_,b,2);}
bool AviWriter::writeU32(uint32_t v){uint8_t b[4]={uint8_t(v),uint8_t(v>>8),uint8_t(v>>16),uint8_t(v>>24)};return writeBytes(avi_,b,4);}
bool AviWriter::patchU32(uint32_t offset,uint32_t value){uint32_t back=avi_.position();if(!avi_.seek(offset)||!writeU32(value)||!avi_.seek(back)){error_="AVI_PATCH_FAILED";return false;}return true;}
bool AviWriter::begin(const String &path,uint16_t width,uint16_t height,uint8_t fps){
  partial_=path;width_=width;height_=height;fps_=fps;frames_=bytes_=0;error_="";
  indexPath_=path+".idx.tmp";if(SD.exists(path)||SD.exists(indexPath_)){error_="AVI_DESTINATION_EXISTS";return false;}
  avi_=SD.open(path,FILE_WRITE);index_=SD.open(indexPath_,FILE_WRITE);if(!avi_||!index_){error_="AVI_OPEN_FAILED";abort();return false;}
  if(!writeFourCC("RIFF")){error_="AVI_HEADER_WRITE_FAILED";abort();return false;}riffSizeOffset_=avi_.position();writeU32(0);writeFourCC("AVI ");
  writeFourCC("LIST");writeU32(192);writeFourCC("hdrl");
  writeFourCC("avih");writeU32(56);writeU32(1000000UL/fps_);writeU32(0);writeU32(0);writeU32(0x10);
  totalFramesOffset_=avi_.position();writeU32(0);writeU32(0);writeU32(1);writeU32(width_*height_*3);writeU32(width_);writeU32(height_);for(int i=0;i<4;i++)writeU32(0);
  writeFourCC("LIST");writeU32(116);writeFourCC("strl");writeFourCC("strh");writeU32(56);writeFourCC("vids");writeFourCC("MJPG");
  writeU32(0);writeU16(0);writeU16(0);writeU32(0);writeU32(1);writeU32(fps_);writeU32(0);
  streamLengthOffset_=avi_.position();writeU32(0);writeU32(width_*height_*3);writeU32(0xffffffff);writeU32(0);
  writeU16(0);writeU16(0);writeU16(width_);writeU16(height_);
  writeFourCC("strf");writeU32(40);writeU32(40);writeU32(width_);writeU32(height_);writeU16(1);writeU16(24);writeFourCC("MJPG");writeU32(width_*height_*3);writeU32(0);writeU32(0);writeU32(0);writeU32(0);
  writeFourCC("LIST");moviSizeOffset_=avi_.position();writeU32(0);moviTypeOffset_=avi_.position();writeFourCC("movi");
  if(!avi_){error_="AVI_HEADER_WRITE_FAILED";abort();return false;}bytes_=avi_.size();return true;
}
bool AviWriter::appendJpeg(const uint8_t *data,size_t length){
  if(!avi_||!index_||!data||length<4||data[0]!=0xff||data[1]!=0xd8||data[length-2]!=0xff||data[length-1]!=0xd9){error_="INVALID_JPEG_FRAME";return false;}
  uint32_t chunk=avi_.position(),offset=chunk-moviTypeOffset_;
  if(!writeFourCC("00dc")||!writeU32(length)||avi_.write(data,length)!=length||(length&1&&!avi_.write(uint8_t(0)))){error_="AVI_FRAME_WRITE_FAILED";return false;}
  uint8_t entry[16]={'0','0','d','c',0x10,0,0,0,uint8_t(offset),uint8_t(offset>>8),uint8_t(offset>>16),uint8_t(offset>>24),uint8_t(length),uint8_t(length>>8),uint8_t(length>>16),uint8_t(length>>24)};
  if(index_.write(entry,sizeof(entry))!=sizeof(entry)){error_="AVI_INDEX_WRITE_FAILED";return false;}
  frames_++;bytes_=avi_.size();return true;
}
bool AviWriter::finalize(){
  if(!avi_||!index_||!frames_){error_="AVI_NO_FRAMES";abort();return false;}
  index_.flush();index_.close();uint32_t moviEnd=avi_.position();
  File idx=SD.open(indexPath_,FILE_READ);if(!idx){error_="AVI_INDEX_REOPEN_FAILED";abort();return false;}
  writeFourCC("idx1");writeU32(idx.size());uint8_t buffer[256];while(idx.available()){size_t got=idx.read(buffer,sizeof(buffer));if(avi_.write(buffer,got)!=got){idx.close();error_="AVI_INDEX_COPY_FAILED";abort();return false;}}idx.close();
  uint32_t end=avi_.position();bool ok=patchU32(moviSizeOffset_,moviEnd-moviTypeOffset_)&&patchU32(totalFramesOffset_,frames_)&&patchU32(streamLengthOffset_,frames_)&&patchU32(riffSizeOffset_,end-8);
  avi_.flush();avi_.close();SD.remove(indexPath_);bytes_=end;return ok;
}
void AviWriter::abort(){if(avi_)avi_.close();if(index_)index_.close();if(indexPath_.length())SD.remove(indexPath_);}

