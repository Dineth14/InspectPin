#include "audio_player.h"
#include "config.h"
#include "wav_utils.h"
#include <ESP_I2S.h>
#include <SD.h>
#include <driver/gpio.h>
#include <driver/rtc_io.h>
// MAX98357A SD_MODE control (single-layer PCB): HIGH = amplifier off, LOW = on.
// Without the control pin (older boards) these are no-ops.
void Amp::begin(){
  if(Config::ampOff<0) return;
  gpio_hold_dis(gpio_num_t(Config::ampOff)); // release hold left by deep sleep
  pinMode(Config::ampOff,OUTPUT); digitalWrite(Config::ampOff,HIGH);
}
void Amp::enable(bool on){ if(Config::ampOff>=0) digitalWrite(Config::ampOff,on?LOW:HIGH); }
void Amp::shutdownForSleep(){
  if(Config::ampOff<0) return;
  digitalWrite(Config::ampOff,HIGH);
  gpio_hold_en(gpio_num_t(Config::ampOff)); gpio_deep_sleep_hold_en();
}
namespace { uint8_t volumePercent=100; }
void setPlaybackVolume(uint8_t percent){volumePercent=percent>100?100:percent;}
uint8_t playbackVolume(){return volumePercent;}
bool recordingCue(bool starting) {
  I2SClass speaker;
  speaker.setPins(Config::bclk, Config::ws, Config::dout);
  if (!speaker.begin(I2S_MODE_STD,16000,I2S_DATA_BIT_WIDTH_16BIT,I2S_SLOT_MODE_STEREO)) return false;
  Amp::enable(true);
  delay(10);
  int16_t block[160];
  for (int i=0; i<80; ++i) {
    int16_t sample = (i % (starting ? 16 : 32) < (starting ? 8 : 16)) ? 2200 : -2200;
    block[2*i]=block[2*i+1]=sample;
  }
  bool ok=true;
  for (int i=0; i<24 && ok; ++i) {
    size_t sent=0;
    ok=i2s_channel_write(speaker.txChan(),block,sizeof(block),&sent,100)==ESP_OK && sent==sizeof(block);
  }
  delay(40);
  speaker.end();
  Amp::enable(false);
  return ok;
}
bool playWav(const String &path) {
  File f=SD.open(path,FILE_READ); uint32_t remaining=0;
  if (!Wav::validate(f,remaining) || f.size()>Config::maxAnswerBytes) { f.close(); Serial.println("Invalid playback WAV"); return false; }
  I2SClass speaker;
  speaker.setPins(Config::bclk,Config::ws,Config::dout);
  if (!speaker.begin(I2S_MODE_STD,16000,I2S_DATA_BIT_WIDTH_16BIT,I2S_SLOT_MODE_STEREO)) { Amp::enable(false); f.close(); return false; }
  Amp::enable(true); delay(10);
  Serial.println("Speaker playback started");
  int16_t mono[256],stereo[512]; bool ok=true;
  uint32_t started=millis(),deadline=remaining/32+5000;
  while (remaining && millis()-started<deadline) {
    size_t want=min(size_t(remaining),sizeof(mono)),got=f.read((uint8_t*)mono,want);
    if (got!=want) { ok=false; break; }
    const float gain=Config::playbackGain*(volumePercent/100.0f);
    for (size_t i=0;i<got/2;i++) stereo[2*i]=stereo[2*i+1]=int16_t(mono[i]*gain);
    size_t sent=0;
    if (i2s_channel_write(speaker.txChan(),stereo,got*2,&sent,1000)!=ESP_OK || sent!=got*2) { ok=false; break; }
    remaining-=got; delay(1);
  }
  delay(100); speaker.end(); Amp::enable(false); f.close();
  Serial.println(ok && !remaining?"Playback finished":"Playback failed"); return ok && !remaining;
}
