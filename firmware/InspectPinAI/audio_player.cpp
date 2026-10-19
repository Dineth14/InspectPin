#include "audio_player.h"
#include "config.h"
#include "wav_utils.h"
#include <ESP_I2S.h>
#include <SD.h>
bool playWav(const String &path) {
  File f=SD.open(path,FILE_READ); uint32_t remaining=0;
  if (!Wav::validate(f,remaining) || f.size()>Config::maxAnswerBytes) { f.close(); Serial.println("Invalid playback WAV"); return false; }
  I2SClass speaker;
  speaker.setPins(Config::bclk,Config::ws,Config::dout);
  if (!speaker.begin(I2S_MODE_STD,16000,I2S_DATA_BIT_WIDTH_16BIT,I2S_SLOT_MODE_STEREO)) { f.close(); return false; }
  Serial.println("Speaker playback started");
  int16_t mono[256],stereo[512]; bool ok=true;
  uint32_t started=millis(),deadline=remaining/32+5000;
  while (remaining && millis()-started<deadline) {
    size_t want=min(size_t(remaining),sizeof(mono)),got=f.read((uint8_t*)mono,want);
    if (got!=want) { ok=false; break; }
    for (size_t i=0;i<got/2;i++) stereo[2*i]=stereo[2*i+1]=int16_t(mono[i]*Config::playbackGain);
    size_t sent=0;
    if (i2s_channel_write(speaker.txChan(),stereo,got*2,&sent,1000)!=ESP_OK || sent!=got*2) { ok=false; break; }
    remaining-=got; delay(1);
  }
  delay(100); speaker.end(); f.close();
  Serial.println(ok && !remaining?"Playback finished":"Playback failed"); return ok && !remaining;
}
