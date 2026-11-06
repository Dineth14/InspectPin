#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <ESP_I2S.h>
#include <esp_camera.h>
#include <esp_system.h>
#include <cmath>

// InspectPin Rev N factory firmware, reconciled to REV N/project netlist.
namespace Pin { constexpr int ntc=1,din=2,reserved=3,flash=4,sda=5,scl=6,sdSck=7,sdMiso=8,sdMosi=9,sdCs=21,bclk=43,lrclk=44,micData=41,micClock=42; }
namespace Pcf { constexpr uint8_t address=0x20,photo=0,ask=1,green=2,usbN=3,chargeN=4,unused=5,red=6,sdDetectN=7; }
constexpr uint8_t INA=0x40;
constexpr float SHUNT_OHMS=0.1f,CURRENT_LSB=0.0001f;
uint8_t pcfLatch=0xff;
bool i2cReady=false,sdReady=false;
RTC_DATA_ATTR uint32_t watchdogCookie=0;

void result(const char *test,const char *status,const String &detail="",const String &measurement="",const String &tolerance=""){
  Serial.printf("{\"type\":\"fct\",\"test\":\"%s\",\"status\":\"%s\",\"detail\":\"%s\",\"measurement\":\"%s\",\"tolerance\":\"%s\"}\n",test,status,detail.c_str(),measurement.c_str(),tolerance.c_str());
  Serial.printf("FCTCSV,%s,%s,%s,%s,%s\n",test,status,detail.c_str(),measurement.c_str(),tolerance.c_str());
}
bool i2cProbe(uint8_t address){Wire.beginTransmission(address);return Wire.endTransmission()==0;}
bool pcfWrite(){Wire.beginTransmission(Pcf::address);Wire.write(pcfLatch);return Wire.endTransmission()==0;}
bool pcfRead(uint8_t &value){if(Wire.requestFrom(int(Pcf::address),1)!=1)return false;value=Wire.read();return true;}
bool pcfSet(uint8_t bit,bool active){if(active)pcfLatch&=~(1U<<bit);else pcfLatch|=1U<<bit;return pcfWrite();}
bool inaWrite(uint8_t reg,uint16_t value){Wire.beginTransmission(INA);Wire.write(reg);Wire.write(value>>8);Wire.write(value);return Wire.endTransmission()==0;}
bool inaRead(uint8_t reg,uint16_t &value){Wire.beginTransmission(INA);Wire.write(reg);if(Wire.endTransmission(false)||Wire.requestFrom(int(INA),2)!=2)return false;value=(uint16_t(Wire.read())<<8)|Wire.read();return true;}

void testBoot(){
  String m=String("chip=")+ESP.getChipModel()+" rev="+ESP.getChipRevision()+" flash="+ESP.getFlashChipSize()+" psram="+ESP.getPsramSize()+" heap="+ESP.getFreeHeap()+" reset="+int(esp_reset_reason());
  result("boot",ESP.getPsramSize()>=8U*1024U*1024U?"PASS":"FAIL","ESP32-S3 boot and memory diagnostics",m,"PSRAM >= 8 MiB");
}
void testI2c(){
  String found;for(uint8_t a=1;a<127;a++)if(i2cProbe(a)){if(found.length())found+=';';found+=String("0x")+String(a,HEX);}
  bool pcf=i2cProbe(Pcf::address),ina=i2cProbe(INA);result("i2c",pcf&&ina?"PASS":"FAIL","expected PCF8574 0x20 and INA219 0x40",found,"both addresses present");
}
void testPcf(){
  uint8_t value=0;bool ok=i2cProbe(Pcf::address)&&pcfWrite()&&pcfRead(value);result("pcf8574",ok?"PASS":"FAIL","latch write and port read",String("port=0x")+String(value,HEX),"I2C ACK and one-byte read");
}
void testButtons(uint32_t timeoutMs=10000){
  uint32_t started=millis();bool photo=false,ask=false;uint8_t value=0xff;
  while(millis()-started<timeoutMs&&!(photo&&ask)){feedLoopWDT();if(pcfRead(value)){photo|=!(value&(1U<<Pcf::photo));ask|=!(value&(1U<<Pcf::ask));}delay(10);}
  result("buttons",photo&&ask?"PASS":"FAIL","press PHOTO and ASK during test window",String("photo=")+photo+" ask="+ask,String("both within ")+timeoutMs+" ms");
}
void testLeds(){
  bool ok=pcfSet(Pcf::green,true);delay(600);ok&=pcfSet(Pcf::green,false);ok&=pcfSet(Pcf::red,true);delay(600);ok&=pcfSet(Pcf::red,false);
  result("led_bus",ok?"PASS":"FAIL","green/red sink commands completed","PCF P2/P6","operator optical confirmation required");
  result("led_visual","BLOCKED","operator or optical fixture must confirm colour and brightness","","green then red visible");
}
void testFlash(){pinMode(Pin::flash,OUTPUT);digitalWrite(Pin::flash,HIGH);delay(500);digitalWrite(Pin::flash,LOW);result("flash_bus","PASS","GPIO4 toggled and returned LOW","GPIO4","operator/current fixture confirmation required");result("flash_visual","BLOCKED","optical/current confirmation not available to firmware","","white LED visible; current within approved fixture limit");}
void beginSd(){SPI.begin(Pin::sdSck,Pin::sdMiso,Pin::sdMosi,Pin::sdCs);sdReady=SD.begin(Pin::sdCs)&&SD.cardType()!=CARD_NONE;}
void testSd(){
  if(!sdReady)beginSd();const char *path="/revn_fct.tmp";bool ok=sdReady;uint8_t pattern[256];for(int i=0;i<256;i++)pattern[i]=uint8_t(i^0xa5);
  if(ok){File f=SD.open(path,FILE_WRITE);ok=f&&f.write(pattern,sizeof(pattern))==sizeof(pattern);if(f){f.flush();f.close();}}
  if(ok){File f=SD.open(path,FILE_READ);for(int i=0;i<256&&ok;i++)ok=f.read()==pattern[i];f.close();}if(SD.exists(path))ok&=SD.remove(path);
  result("sd",ok?"PASS":"FAIL","SPI read/write/integrity",sdReady?String("capacity_mb=")+uint32_t(SD.cardSize()/1024/1024):"no card","256-byte exact pattern and FAT access");
}
camera_config_t cameraConfig(){camera_config_t c={};c.pin_pwdn=-1;c.pin_reset=-1;c.pin_xclk=10;c.pin_sccb_sda=40;c.pin_sccb_scl=39;c.pin_d0=15;c.pin_d1=17;c.pin_d2=18;c.pin_d3=16;c.pin_d4=14;c.pin_d5=12;c.pin_d6=11;c.pin_d7=48;c.pin_vsync=38;c.pin_href=47;c.pin_pclk=13;c.xclk_freq_hz=20000000;c.ledc_timer=LEDC_TIMER_0;c.ledc_channel=LEDC_CHANNEL_0;c.pixel_format=PIXFORMAT_JPEG;c.frame_size=FRAMESIZE_SVGA;c.jpeg_quality=12;c.fb_count=1;c.fb_location=CAMERA_FB_IN_PSRAM;c.grab_mode=CAMERA_GRAB_WHEN_EMPTY;return c;}
void testCamera(){
  camera_config_t c=cameraConfig();esp_err_t init=esp_camera_init(&c);if(init!=ESP_OK){result("camera","FAIL","esp_camera_init failed",String("0x")+String(init,HEX),"OV3660/OV5640 JPEG sensor");return;}
  sensor_t *s=esp_camera_sensor_get();for(int i=0;i<2;i++){camera_fb_t *w=esp_camera_fb_get();if(w)esp_camera_fb_return(w);delay(40);}camera_fb_t *fb=esp_camera_fb_get();
  bool valid=fb&&fb->format==PIXFORMAT_JPEG&&fb->width==800&&fb->height==600&&fb->len>4&&fb->buf[0]==0xff&&fb->buf[1]==0xd8&&fb->buf[fb->len-2]==0xff&&fb->buf[fb->len-1]==0xd9;
  bool saved=false;if(valid){if(!sdReady)beginSd();if(sdReady){File f=SD.open("/revn_factory_camera.jpg",FILE_WRITE);saved=f&&f.write(fb->buf,fb->len)==fb->len;if(f){f.flush();f.close();}}}
  String m=String("pid=0x")+String(s?s->id.PID:0,HEX)+" width="+(fb?fb->width:0)+" height="+(fb?fb->height:0)+" bytes="+(fb?fb->len:0)+" sd="+saved;
  result("camera",valid&&saved?"PASS":"FAIL","genuine JPEG capture and SD persistence",m,"800x600 JPEG SOI/EOI; nonzero file");if(fb)esp_camera_fb_return(fb);esp_camera_deinit();
}
void writeWavHeader(File &f,uint32_t bytes){uint32_t riff=bytes+36,rate=16000,byteRate=32000;uint16_t one=1,bits=16;f.seek(0);f.write((uint8_t*)"RIFF",4);f.write((uint8_t*)&riff,4);f.write((uint8_t*)"WAVEfmt ",8);uint32_t fmt=16;f.write((uint8_t*)&fmt,4);f.write((uint8_t*)&one,2);f.write((uint8_t*)&one,2);f.write((uint8_t*)&rate,4);f.write((uint8_t*)&byteRate,4);uint16_t align=2;f.write((uint8_t*)&align,2);f.write((uint8_t*)&bits,2);f.write((uint8_t*)"data",4);f.write((uint8_t*)&bytes,4);}
void testMic(){
  if(!sdReady)beginSd();if(!sdReady){result("microphone","FAIL","SD unavailable","","valid WAV required");return;}I2SClass mic;mic.setPinsPdmRx(Pin::micClock,Pin::micData);if(!mic.begin(I2S_MODE_PDM_RX,16000,I2S_DATA_BIT_WIDTH_16BIT,I2S_SLOT_MODE_MONO)){result("microphone","FAIL","PDM begin failed");return;}
  File f=SD.open("/revn_factory_mic.wav",FILE_WRITE);writeWavHeader(f,0);uint32_t bytes=0;double squares=0;int peak=0;int16_t buf[512];uint32_t start=millis();bool ok=bool(f);
  while(ok&&millis()-start<5000){feedLoopWDT();size_t got=0;if(i2s_channel_read(mic.rxChan(),buf,sizeof(buf),&got,500)!=ESP_OK||!got){ok=false;break;}ok=f.write((uint8_t*)buf,got)==got;bytes+=got;for(size_t i=0;i<got/2;i++){peak=max(peak,abs(int(buf[i])));squares+=double(buf[i])*buf[i];}}
  writeWavHeader(f,bytes);f.flush();f.close();mic.end();float rms=bytes?sqrt(squares/(bytes/2)):0;ok&=bytes>=150000&&peak>50&&rms>5;
  result("microphone",ok?"PASS":"FAIL","5-second PCM16 mono WAV",String("bytes=")+bytes+" peak="+peak+" rms="+String(rms,1),"bytes >=150000; peak >50; RMS >5");
}
void testSpeaker(){
  I2SClass out;out.setPins(Pin::bclk,Pin::lrclk,Pin::din);if(!out.begin(I2S_MODE_STD,16000,I2S_DATA_BIT_WIDTH_16BIT,I2S_SLOT_MODE_STEREO)){result("speaker_bus","FAIL","I2S begin failed");return;}int16_t stereo[256];for(int block=0;block<125;block++){for(int i=0;i<128;i++){int16_t v=int16_t(6000*sinf(2*PI*880*(block*128+i)/16000.0f));stereo[2*i]=stereo[2*i+1]=v;}size_t sent=0;if(i2s_channel_write(out.txChan(),stereo,sizeof(stereo),&sent,1000)!=ESP_OK||sent!=sizeof(stereo)){out.end();result("speaker_bus","FAIL","I2S write failed");return;}}out.end();result("speaker_bus","PASS","880 Hz digital tone transmitted","1 second","operator/acoustic fixture confirmation required");result("speaker_audio","BLOCKED","firmware cannot hear its own speaker","","audible clean tone");
}
void testIna(){
  uint16_t cal=uint16_t(0.04096f/(CURRENT_LSB*SHUNT_OHMS));uint16_t readCal=0,busRaw=0,shuntRaw=0,currentRaw=0;bool ok=inaWrite(0x00,0x399f)&&inaWrite(0x05,cal)&&inaRead(0x05,readCal)&&inaRead(0x02,busRaw)&&inaRead(0x01,shuntRaw)&&inaRead(0x04,currentRaw);float bus=(busRaw>>3)*0.004f,shunt=int16_t(shuntRaw)*0.01f,current=int16_t(currentRaw)*CURRENT_LSB*1000;ok&=readCal==cal&&bus>2.5f&&bus<4.5f;
  result("ina219",ok?"PASS":"FAIL","register/config/bus measurement",String("bus_v=")+String(bus,3)+" shunt_mv="+String(shunt,3)+" current_ma="+String(current,2)+" cal="+readCal,"2.5<bus<4.5 V; calibration=4096");result("ina219_calibration","BLOCKED","precision current calibration requires fixture load and DMM","","fixture points at >=100 mA and >=500 mA");
}
void testNtc(){analogReadResolution(12);analogSetPinAttenuation(Pin::ntc,ADC_11db);uint32_t total=0;for(int i=0;i<32;i++){total+=analogReadMilliVolts(Pin::ntc);delay(2);}float mv=total/32.0f;bool open=mv>3200,shorted=mv<100;float r=(!open&&!shorted)?10000.0f*mv/(3300.0f-mv):0;float t=(!open&&!shorted)?1.0f/(1.0f/298.15f+logf(r/10000.0f)/3950.0f)-273.15f:0;bool ok=!open&&!shorted&&isfinite(t)&&t>-20&&t<80;result("ntc",ok?"PASS":"FAIL",open?"open circuit":shorted?"short circuit":"ADC and beta estimate",String("mv=")+String(mv,1)+" ohms="+String(r,1)+" c="+String(t,2),"100<ADC<3200 mV; fixture temperature comparison required");}
void testUsb(){uint8_t port=0xff;bool ok=pcfRead(port);bool usb=ok&&!(port&(1U<<Pcf::usbN));result("usb_presence",ok?"PASS":"FAIL","current detector state only",String("usb_present=")+usb,"toggle validation requires fixture disconnect/reconnect");result("usb_transition","BLOCKED","automated power switching fixture not connected");}
void testCharger(){result("charger_status","BLOCKED","Rev N default CHG_SOURCE follows VBUS; actual XIAO NCHG tap must be verified and installed before charging/full claims","PCF P4","verified NCHG low/high transition required");}
void testWatchdog(){result("watchdog_config","PASS","loop watchdog enabled; use wdt_arm for destructive reset/recovery proof",String("reset_reason=")+int(esp_reset_reason()),"wdt_arm must reboot and report watchdog_recovery PASS");}
void runAll(){testBoot();testI2c();testPcf();testSd();testIna();testNtc();testUsb();testCharger();testCamera();result("buttons","BLOCKED","run buttons command with operator");result("led_visual","BLOCKED","run leds with operator/optical fixture");result("flash_visual","BLOCKED","run flash with operator/current fixture");result("microphone","BLOCKED","run mic in controlled acoustic fixture");result("speaker_audio","BLOCKED","run speaker with operator/acoustic fixture");testWatchdog();}
void help(){Serial.println("{\"type\":\"fct_help\",\"commands\":[\"boot\",\"i2c\",\"pcf\",\"buttons\",\"leds\",\"flash\",\"camera\",\"mic\",\"speaker\",\"sd\",\"ina\",\"ntc\",\"usb\",\"charger\",\"watchdog\",\"wdt_arm\",\"all\"]}");}

void setup(){Serial.begin(115200);uint32_t wait=millis();while(!Serial&&millis()-wait<3000)delay(10);pinMode(Pin::reserved,INPUT);pinMode(Pin::flash,OUTPUT);digitalWrite(Pin::flash,LOW);Wire.begin(Pin::sda,Pin::scl,100000);i2cReady=true;enableLoopWDT();pcfWrite();if(watchdogCookie==0x49505744&&esp_reset_reason()==ESP_RST_TASK_WDT)result("watchdog_recovery","PASS","watchdog reset observed and firmware recovered");watchdogCookie=0;Serial.println("{\"type\":\"fct_ready\",\"firmware\":\"InspectPin Rev N Factory Test\",\"version\":\"1.0.0\"}");help();}
void loop(){feedLoopWDT();if(!Serial.available()){delay(5);return;}String command=Serial.readStringUntil('\n');command.trim();command.toLowerCase();if(command=="boot")testBoot();else if(command=="i2c")testI2c();else if(command=="pcf")testPcf();else if(command=="buttons")testButtons();else if(command=="leds")testLeds();else if(command=="flash")testFlash();else if(command=="camera")testCamera();else if(command=="mic")testMic();else if(command=="speaker")testSpeaker();else if(command=="sd")testSd();else if(command=="ina")testIna();else if(command=="ntc")testNtc();else if(command=="usb")testUsb();else if(command=="charger")testCharger();else if(command=="watchdog")testWatchdog();else if(command=="all")runAll();else if(command=="wdt_arm"){watchdogCookie=0x49505744;result("watchdog_arm","PASS","intentional watchdog reset armed");Serial.flush();while(true){} }else help();}
