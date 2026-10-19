#include "wav_utils.h"
#include "config.h"
#include <cstring>
namespace {
void put16(uint8_t *p, uint16_t n) { p[0] = n; p[1] = n >> 8; }
void put32(uint8_t *p, uint32_t n) { for (int i=0;i<4;i++) p[i] = n >> (8*i); }
uint16_t get16(const uint8_t *p) { return p[0] | (uint16_t(p[1]) << 8); }
uint32_t get32(const uint8_t *p) { return uint32_t(p[0]) | (uint32_t(p[1])<<8) | (uint32_t(p[2])<<16) | (uint32_t(p[3])<<24); }
}
bool Wav::writeHeader(File &f, uint32_t bytes) {
  uint8_t h[44] = {};
  memcpy(h,"RIFF",4); put32(h+4,bytes+36); memcpy(h+8,"WAVEfmt ",8);
  put32(h+16,16); put16(h+20,1); put16(h+22,1); put32(h+24,Config::sampleRate);
  put32(h+28,Config::sampleRate*2); put16(h+32,2); put16(h+34,16);
  memcpy(h+36,"data",4); put32(h+40,bytes);
  return f.seek(0) && f.write(h,44)==44;
}
bool Wav::validate(File &f, uint32_t &pcmBytes) {
  uint8_t h[44];
  if (!f || !f.seek(0) || f.read(h,44)!=44) return false;
  pcmBytes = get32(h+40);
  return !memcmp(h,"RIFF",4) && !memcmp(h+8,"WAVEfmt ",8) && !memcmp(h+36,"data",4)
    && get32(h+16)==16 && get16(h+20)==1 && get16(h+22)==1 && get32(h+24)==16000
    && get32(h+28)==32000 && get16(h+32)==2 && get16(h+34)==16 && pcmBytes>0
    && pcmBytes%2==0 && uint64_t(pcmBytes)+44==f.size() && uint64_t(get32(h+4))+8==f.size();
}
