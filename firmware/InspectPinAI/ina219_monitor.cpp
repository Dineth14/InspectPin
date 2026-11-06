#include "ina219_monitor.h"
#include "config.h"
#include "hardware_profile.h"
#include <Wire.h>
#include <cmath>

namespace {
constexpr uint8_t REG_CONFIG=0x00,REG_SHUNT=0x01,REG_BUS=0x02,REG_POWER=0x03,REG_CURRENT=0x04,REG_CAL=0x05;
constexpr uint16_t CONFIG_CONTINUOUS_12BIT=0x399f;
Ina219::Reading current;
bool ready=false;
uint16_t calibration=0;
bool writeRegister(uint8_t reg,uint16_t value){Wire.beginTransmission(HardwareProfile::ina219Address);Wire.write(reg);Wire.write(value>>8);Wire.write(value&0xff);return Wire.endTransmission()==0;}
bool readRegister(uint8_t reg,uint16_t &value){Wire.beginTransmission(HardwareProfile::ina219Address);Wire.write(reg);if(Wire.endTransmission(false)!=0||Wire.requestFrom(int(HardwareProfile::ina219Address),2)!=2)return false;value=(uint16_t(Wire.read())<<8)|Wire.read();return true;}
}

bool Ina219::begin(){
  if(!IP_INA219_ENABLED)return false;
  const float computed=0.04096f/(IP_INA219_CURRENT_LSB_AMPS*IP_INA219_SHUNT_OHMS);
  if(!std::isfinite(computed)||computed<1||computed>65535){Serial.println("INA219 calibration constants invalid");return false;}
  calibration=uint16_t(computed);uint16_t probe=0;
  ready=writeRegister(REG_CONFIG,CONFIG_CONTINUOUS_12BIT)&&writeRegister(REG_CAL,calibration)&&readRegister(REG_CAL,probe)&&probe==calibration;
  Serial.printf("INA219 %s address=0x%02x shunt=%.4f ohm current_lsb=%.6f A calibration=%u\n",ready?"ready":"FAILED",HardwareProfile::ina219Address,IP_INA219_SHUNT_OHMS,IP_INA219_CURRENT_LSB_AMPS,calibration);
  return ready;
}

Ina219::Reading Ina219::sample(){
  if(!ready)return current;
  double busSum=0,shuntSum=0,currentSum=0,powerSum=0;unsigned good=0;
  for(unsigned i=0;i<8;i++){
    uint16_t busRaw=0,shuntRaw=0,currentRaw=0,powerRaw=0;
    if(readRegister(REG_BUS,busRaw)&&readRegister(REG_SHUNT,shuntRaw)&&readRegister(REG_CURRENT,currentRaw)&&readRegister(REG_POWER,powerRaw)&&!(busRaw&1U)){
      const float bus=(busRaw>>3)*0.004f;const float shunt=int16_t(shuntRaw)*0.01f;const float amps=int16_t(currentRaw)*IP_INA219_CURRENT_LSB_AMPS;
      busSum+=bus;shuntSum+=shunt;currentSum+=amps*1000.0f;powerSum+=powerRaw*(20.0f*IP_INA219_CURRENT_LSB_AMPS)*1000.0f;good++;
    }
    delay(3);
  }
  if(!good){current.valid=false;current.sampledAt=millis();return current;}
  current.busVolts=busSum/good;current.shuntMillivolts=shuntSum/good;current.packVolts=current.busVolts+current.shuntMillivolts/1000.0f;
  current.currentMilliamps=currentSum/good;current.powerMilliwatts=powerSum/good;
  current.valid=std::isfinite(current.packVolts)&&current.packVolts>2.5f&&current.packVolts<4.5f&&fabsf(current.shuntMillivolts)<320.0f;
  current.sampledAt=millis();return current;
}
Ina219::Reading Ina219::latest(){return current;}
bool Ina219::available(){return ready;}
uint16_t Ina219::calibrationRegister(){return calibration;}
