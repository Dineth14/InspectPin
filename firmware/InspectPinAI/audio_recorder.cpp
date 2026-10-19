#include "audio_recorder.h"
#include "config.h"
#include "wav_utils.h"
#include <ESP_I2S.h>
#include <SD.h>
#include <cmath>
bool recordWav(const String &path) {
  I2SClass mic;
  mic.setPinsPdmRx(Config::micClock,Config::micData);
  if (!mic.begin(I2S_MODE_PDM_RX,16000,I2S_DATA_BIT_WIDTH_16BIT,I2S_SLOT_MODE_MONO)) {
    Serial.println("Microphone I2S initialization failed"); return false;
  }
  File f=SD.open(path,FILE_WRITE);
  if (!f || !Wav::writeHeader(f,0)) { f.close(); mic.end(); return false; }
  Serial.println("Microphone recording started");
  const uint32_t target=Config::recordSeconds*32000;
  uint32_t written=0, started=millis(); int peak=0; double squares=0;
  int16_t buf[512]; bool ok=true;
  while (written<target && millis()-started<Config::recordSeconds*1000+3000) {
    size_t got=0, want=min(size_t(target-written),sizeof(buf));
    esp_err_t err=i2s_channel_read(mic.rxChan(),buf,want,&got,500);
    if (err!=ESP_OK || !got || got%2) { ok=false; break; }
    size_t saved=f.write((uint8_t*)buf,got); written+=saved;
    if (saved!=got) { ok=false; break; }
    for (size_t i=0;i<got/2;i++) { int sample=buf[i]; peak=max(peak,abs(sample)); squares+=double(sample)*sample; }
    delay(1);
  }
  // Keep even a partial recording for diagnosis; only complete captures are uploaded.
  ok=Wav::writeHeader(f,written) && ok && written==target;
  f.flush(); f.close(); mic.end();
  Serial.printf("WAV saved: %s bytes=%lu peak=%d RMS=%.1f complete=%s\n",path.c_str(),(unsigned long)(written+44),peak,written?sqrt(squares/(written/2)):0,ok?"yes":"no");
  return ok;
}
