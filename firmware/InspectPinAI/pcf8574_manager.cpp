#include "pcf8574_manager.h"
#include <Wire.h>
#include "config.h"
#include "hardware_profile.h"

namespace {
bool ready=false;
uint8_t outputLatch=0xff,portValue=0xff;
uint32_t lastRead=0;
bool writePort(){
  if(!ready)return false;
  Wire.beginTransmission(HardwareProfile::pcfAddress);
  Wire.write(outputLatch);
  return Wire.endTransmission()==0;
}
bool readPort(){
  if(!ready)return false;
  if(Wire.requestFrom(int(HardwareProfile::pcfAddress),1)!=1)return false;
  portValue=Wire.read();lastRead=millis();return true;
}
bool setActiveLow(uint8_t bit,bool enabled){
  if(!ready||bit>7)return false;
  if(enabled)outputLatch&=~(1U<<bit);else outputLatch|=(1U<<bit);
  return writePort();
}
}

bool Expander::begin(){
  if(!IP_PCF8574_ENABLED)return false;
  Wire.begin(HardwareProfile::pcfSdaGpio,HardwareProfile::pcfSclGpio,100000);
  pinMode(HardwareProfile::pcfInterruptGpio,INPUT_PULLUP);
  Wire.beginTransmission(HardwareProfile::pcfAddress);
  ready=Wire.endTransmission()==0;
  outputLatch=0xff; // P0/P1 HIGH -> inverter outputs LOW -> loads OFF.
  if(!ready||!writePort()||!readPort()){ready=false;Serial.println("PCF8574 unavailable; external controls disabled");return false;}
  Serial.printf("PCF8574 ready address=0x%02x port=0x%02x\n",HardwareProfile::pcfAddress,portValue);
  return true;
}
void Expander::tick(){if(ready&&millis()-lastRead>=10)readPort();}
bool Expander::available(){return ready;}
bool Expander::photoPressed(){return ready&&!(portValue&(1U<<HardwareProfile::pcfPhotoButton));}
bool Expander::setFlashlight(bool enabled){return setActiveLow(HardwareProfile::pcfFlashlight,enabled);}
bool Expander::setVibration(bool enabled){return setActiveLow(HardwareProfile::pcfVibration,enabled);}
bool Expander::inputLow(uint8_t bit){return ready&&bit<8&&!(portValue&(1U<<bit));}
bool Expander::prepareForSleep(){
  if(!ready)return !IP_PCF8574_ENABLED;
  setActiveLow(HardwareProfile::pcfFlashlight,false);
  setActiveLow(HardwareProfile::pcfVibration,false);
  return readPort()&&digitalRead(HardwareProfile::pcfInterruptGpio)==HIGH;
}
uint8_t Expander::latestPort(){return portValue;}

