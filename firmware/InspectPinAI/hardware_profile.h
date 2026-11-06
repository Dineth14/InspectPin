#pragma once
#include <stdint.h>

// Reconciled Rev E specification. Physical enabling remains gated until the
// missing KiCad source is reviewed and the assembled nets are continuity-tested.
namespace HardwareProfile {
#if defined(IP_USE_REV_N_CONFIG)
// Rev N values reconciled against the KiCad PCB/netlist and PCBKit source
// supplied in REV N/ on 2026-11-05. Quasi-bidirectional inputs stay HIGH.
constexpr int askButtonGpio = -1;      // ASK is PCF8574 P1. GPIO3 is reserved.
constexpr int pcfInterruptGpio = -1;   // No interrupt GPIO was specified; polling only.
constexpr int batteryAdcGpio = -1;     // INA219 replaces the Rev E divider.
constexpr int pcfSdaGpio = 5;
constexpr int pcfSclGpio = 6;
constexpr int ntcGpio = 1;
constexpr int flashlightGpio = 4;
constexpr int speakerDataGpio = 2;
constexpr int speakerBclkGpio = 43;
constexpr int speakerLrclkGpio = 44;
constexpr int hapticGpio = -1;
constexpr int reservedGpio = 3;
constexpr uint8_t pcfAddress = 0x20;
constexpr uint8_t ina219Address = 0x40;

constexpr uint8_t pcfPhotoButton = 0;  // PHOTO_N, active low.
constexpr uint8_t pcfAskButton = 1;    // ASK_N, active low.
constexpr uint8_t pcfStatusLed = 2;    // CHARGE_LED_K, active-low sink.
constexpr uint8_t pcfUsbPresentN = 3;  // USB_PRESENT_N, low when USB is inserted.
constexpr uint8_t pcfChargeN = 4;      // CHG_STATUS_N: HIGH=charging only with verified NCHG tap.
constexpr uint8_t pcfSpare = 5;        // Unconnected in KiCad.
constexpr uint8_t pcfFaultLed = 6;     // FAULT_LED_K, active-low sink.
constexpr uint8_t pcfCardDetectN = 7;  // SD_CD_N, low when optional switch closes.
constexpr uint8_t pcfChargeFullN = pcfChargeN; // Compatibility only; not a full signal.
constexpr uint8_t pcfChargeValidN = pcfSpare;
constexpr uint8_t pcfFlashlight = pcfSpare;
constexpr uint8_t pcfVibration = pcfSpare;
#else
constexpr int askButtonGpio = 3;       // XIAO D2; strap precaution applies.
constexpr int pcfInterruptGpio = 5;    // XIAO D4; RTC GPIO, active-low INT.
constexpr int batteryAdcGpio = 6;      // XIAO D5; 100k/100k divider midpoint.
constexpr int pcfSdaGpio = 43;         // XIAO D6.
constexpr int pcfSclGpio = 44;         // XIAO D7.
constexpr uint8_t pcfAddress = 0x20;   // PCF8574 A2:A0 tied low.

constexpr uint8_t pcfFlashlight = 0;   // Active-low before fail-safe inverter.
constexpr uint8_t pcfVibration = 1;    // Active-low before fail-safe inverter.
constexpr uint8_t pcfPhotoButton = 3;  // Button to GND; HIGH when released.
constexpr uint8_t pcfUsbPresentN = 4;  // Decoder open drain: LOW = USB present.
constexpr uint8_t pcfChargeFullN = 5;  // Decoder open drain: LOW = full.
constexpr uint8_t pcfChargeValidN = 6; // Decoder open drain: LOW = status valid.
constexpr uint8_t pcfSpare = 7;
constexpr uint8_t pcfAskButton = 2;
constexpr uint8_t pcfStatusLed = 2;
constexpr uint8_t pcfFaultLed = 7;
constexpr uint8_t pcfChargeN = 5;
constexpr uint8_t pcfCardDetectN = 7;
constexpr uint8_t ina219Address = 0x40;
constexpr int ntcGpio = -1;
constexpr int flashlightGpio = 43;
constexpr int speakerDataGpio = 4;
constexpr int speakerBclkGpio = 1;
constexpr int speakerLrclkGpio = 2;
constexpr int hapticGpio = 44;
constexpr int reservedGpio = -1;
#endif

#if !defined(IP_USE_REV_N_CONFIG)
static_assert(askButtonGpio != batteryAdcGpio, "ASK and battery ADC conflict");
static_assert(pcfInterruptGpio != batteryAdcGpio, "PCF INT and battery ADC conflict");
#endif
static_assert(pcfSdaGpio != pcfSclGpio, "I2C SDA/SCL conflict");
}

