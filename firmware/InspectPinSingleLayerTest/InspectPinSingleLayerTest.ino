#include <Arduino.h>
#include <SPI.h>
#include <SD.h>
#include <ESP_I2S.h>
#include <esp_camera.h>
#include <esp_sleep.h>
#include <driver/gpio.h>
#include <cmath>

namespace Pin {
constexpr int bclk=1,lrc=2,din=4,ask=5,ampOff=6,photo=44;
constexpr int sdSck=7,sdMiso=8,sdMosi=9,sdCs=21;
constexpr int micData=41,micClock=42;
}

bool sdReady=false;

void result(const char *test,const char *status,const String &detail="",const String &measurement="") {
  Serial.printf("{\"type\":\"single_layer_test\",\"test\":\"%s\",\"status\":\"%s\",\"detail\":\"%s\",\"measurement\":\"%s\"}\n",
                test,status,detail.c_str(),measurement.c_str());
}

void amp(bool enabled){digitalWrite(Pin::ampOff,enabled?LOW:HIGH);}

void testBoot(){
  String wake="power/reset";
  if(esp_sleep_get_wakeup_cause()==ESP_SLEEP_WAKEUP_EXT1)wake="ASK/GPIO5";
  bool ok=ESP.getPsramSize()>=8U*1024U*1024U;
  result("boot",ok?"PASS":"FAIL","ESP32-S3 and PSRAM",String("psram=")+ESP.getPsramSize()+" heap="+ESP.getFreeHeap()+" wake="+wake);
}

void testLevels(){
  result("button_levels","PASS","LOW means pressed",String("ask_gpio5=")+(digitalRead(Pin::ask)?"HIGH":"LOW")+" photo_gpio44="+(digitalRead(Pin::photo)?"HIGH":"LOW"));
}

void testButtons(uint32_t timeoutMs=10000){
  bool ask=false,photo=false;uint32_t start=millis();
  while(millis()-start<timeoutMs&&!(ask&&photo)){ask|=digitalRead(Pin::ask)==LOW;photo|=digitalRead(Pin::photo)==LOW;delay(10);}
  result("buttons",ask&&photo?"PASS":"FAIL","press ASK and PHOTO during ten-second window",String("ask=")+ask+" photo="+photo);
}

void beginSd(){SPI.begin(Pin::sdSck,Pin::sdMiso,Pin::sdMosi,Pin::sdCs);sdReady=SD.begin(Pin::sdCs)&&SD.cardType()!=CARD_NONE;}
void testSd(){
  if(!sdReady)beginSd();const char *path="/single_layer_test.tmp";uint8_t data[256];for(int i=0;i<256;i++)data[i]=uint8_t(i^0x5a);bool ok=sdReady;
  if(ok){File f=SD.open(path,FILE_WRITE);ok=f&&f.write(data,sizeof(data))==sizeof(data);if(f){f.flush();f.close();}}
  if(ok){File f=SD.open(path,FILE_READ);for(int i=0;i<256&&ok;i++)ok=f.read()==data[i];if(f)f.close();}
  if(SD.exists(path))ok&=SD.remove(path);
  result("sd",ok?"PASS":"FAIL","microSD exact write/read/remove",sdReady?String("capacity_mb=")+uint32_t(SD.cardSize()/1024/1024):"no card");
}

camera_config_t cameraConfig(){
  camera_config_t c={};c.pin_pwdn=-1;c.pin_reset=-1;c.pin_xclk=10;c.pin_sccb_sda=40;c.pin_sccb_scl=39;
  c.pin_d0=15;c.pin_d1=17;c.pin_d2=18;c.pin_d3=16;c.pin_d4=14;c.pin_d5=12;c.pin_d6=11;c.pin_d7=48;
  c.pin_vsync=38;c.pin_href=47;c.pin_pclk=13;c.xclk_freq_hz=20000000;c.ledc_timer=LEDC_TIMER_0;c.ledc_channel=LEDC_CHANNEL_0;
  c.pixel_format=PIXFORMAT_JPEG;c.frame_size=FRAMESIZE_SVGA;c.jpeg_quality=12;c.fb_count=1;c.fb_location=CAMERA_FB_IN_PSRAM;c.grab_mode=CAMERA_GRAB_WHEN_EMPTY;return c;
}
void testCamera(){
  camera_config_t c=cameraConfig();esp_err_t init=esp_camera_init(&c);if(init!=ESP_OK){result("camera","FAIL","initialization",String("error=0x")+String(init,HEX));return;}
  for(int i=0;i<2;i++){camera_fb_t *warm=esp_camera_fb_get();if(warm)esp_camera_fb_return(warm);delay(40);}
  camera_fb_t *fb=esp_camera_fb_get();sensor_t *sensor=esp_camera_sensor_get();
  bool jpeg=fb&&fb->format==PIXFORMAT_JPEG&&fb->width==800&&fb->height==600&&fb->len>4&&fb->buf[0]==0xff&&fb->buf[1]==0xd8&&fb->buf[fb->len-2]==0xff&&fb->buf[fb->len-1]==0xd9;
  bool saved=false;if(jpeg){if(!sdReady)beginSd();if(sdReady){SD.remove("/single_layer_camera.jpg");File f=SD.open("/single_layer_camera.jpg",FILE_WRITE);saved=f&&f.write(fb->buf,fb->len)==fb->len;if(f){f.flush();f.close();}}}
  result("camera",jpeg&&saved?"PASS":"FAIL","800x600 JPEG saved to SD",String("pid=0x")+String(sensor?sensor->id.PID:0,HEX)+" bytes="+(fb?fb->len:0)+" saved="+saved);
  if(fb)esp_camera_fb_return(fb);esp_camera_deinit();
}

void writeWavHeader(File &f,uint32_t bytes){
  uint32_t riff=bytes+36,rate=16000,byteRate=32000,fmt=16;uint16_t one=1,bits=16,align=2;
  f.seek(0);f.write((uint8_t*)"RIFF",4);f.write((uint8_t*)&riff,4);f.write((uint8_t*)"WAVEfmt ",8);f.write((uint8_t*)&fmt,4);
  f.write((uint8_t*)&one,2);f.write((uint8_t*)&one,2);f.write((uint8_t*)&rate,4);f.write((uint8_t*)&byteRate,4);f.write((uint8_t*)&align,2);f.write((uint8_t*)&bits,2);f.write((uint8_t*)"data",4);f.write((uint8_t*)&bytes,4);
}
void testMic(){
  if(!sdReady)beginSd();if(!sdReady){result("microphone","FAIL","SD unavailable");return;}
  I2SClass mic;mic.setPinsPdmRx(Pin::micClock,Pin::micData);if(!mic.begin(I2S_MODE_PDM_RX,16000,I2S_DATA_BIT_WIDTH_16BIT,I2S_SLOT_MODE_MONO)){result("microphone","FAIL","PDM start");return;}
  SD.remove("/single_layer_mic.wav");File f=SD.open("/single_layer_mic.wav",FILE_WRITE);bool ok=bool(f);if(ok)writeWavHeader(f,0);
  uint32_t bytes=0,start=millis();double squares=0;int peak=0;int16_t samples[512];
  while(ok&&millis()-start<5000){size_t got=0;if(i2s_channel_read(mic.rxChan(),samples,sizeof(samples),&got,500)!=ESP_OK||!got){ok=false;break;}ok=f.write((uint8_t*)samples,got)==got;bytes+=got;for(size_t i=0;i<got/2;i++){int v=samples[i];peak=max(peak,abs(v));squares+=double(v)*v;}}
  if(f){writeWavHeader(f,bytes);f.flush();f.close();}mic.end();float rms=bytes?sqrt(squares/(bytes/2)):0;ok&=bytes>=150000&&peak>50&&rms>5;
  result("microphone",ok?"PASS":"FAIL","five-second PCM16 WAV",String("bytes=")+bytes+" peak="+peak+" rms="+String(rms,1));
}

void testSpeaker(){
  I2SClass out;out.setPins(Pin::bclk,Pin::lrc,Pin::din);if(!out.begin(I2S_MODE_STD,16000,I2S_DATA_BIT_WIDTH_16BIT,I2S_SLOT_MODE_STEREO)){amp(false);result("speaker_bus","FAIL","I2S start");return;}
  amp(true);delay(10);bool ok=true;int16_t stereo[512];
  for(int block=0;block<125&&ok;block++){for(int i=0;i<256;i+=2){int16_t v=int16_t(12000*sinf(2*PI*880*(block*128+i/2)/16000.0f));stereo[i]=stereo[i+1]=v;}size_t sent=0;ok=i2s_channel_write(out.txChan(),stereo,sizeof(stereo),&sent,1000)==ESP_OK&&sent==sizeof(stereo);}
  delay(50);out.end();amp(false);result("speaker_bus",ok?"PASS":"FAIL","880 Hz tone; operator confirms sound","GPIO6 returned HIGH/off");
}

void enterSleep(){
  if(digitalRead(Pin::ask)==LOW){result("sleep","FAIL","release ASK before sleep");return;}
  amp(false);gpio_hold_en(gpio_num_t(Pin::ampOff));gpio_deep_sleep_hold_en();
  esp_sleep_enable_ext1_wakeup_io(1ULL<<Pin::ask,ESP_EXT1_WAKEUP_ANY_LOW);
  result("sleep","PASS","entering deep sleep; press ASK to wake");Serial.flush();delay(50);esp_deep_sleep_start();
}

void help(){Serial.println("Commands: d=levels b=buttons s=SD c=camera m=mic p=speaker z=sleep h=help");}

void setup(){
  Serial.begin(115200);uint32_t start=millis();while(!Serial&&millis()-start<5000)delay(10);
  gpio_hold_dis(gpio_num_t(Pin::ampOff));pinMode(Pin::ampOff,OUTPUT);amp(false);pinMode(Pin::ask,INPUT);pinMode(Pin::photo,INPUT);
  Serial.println("InspectPin single-layer hardware test ready");testBoot();testLevels();help();
}
void loop(){
  static uint32_t heartbeat=0;if(millis()-heartbeat>=2000){heartbeat=millis();Serial.printf("HEARTBEAT ask=%s photo=%s amp_off=HIGH\n",digitalRead(Pin::ask)?"HIGH":"LOW",digitalRead(Pin::photo)?"HIGH":"LOW");}
  if(!Serial.available()){delay(5);return;}char command=Serial.read();
  if(command=='d')testLevels();else if(command=='b')testButtons();else if(command=='s')testSd();else if(command=='c')testCamera();else if(command=='m')testMic();else if(command=='p')testSpeaker();else if(command=='z')enterSleep();else if(command=='h')help();
}
