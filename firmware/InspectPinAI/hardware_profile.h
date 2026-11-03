#pragma once
#include <stdint.h>

// Reconciled Rev E specification. Physical enabling remains gated until the
// missing KiCad source is reviewed and the assembled nets are continuity-tested.
namespace HardwareProfile {
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

static_assert(askButtonGpio != batteryAdcGpio, "ASK and battery ADC conflict");
static_assert(pcfInterruptGpio != batteryAdcGpio, "PCF INT and battery ADC conflict");
static_assert(pcfSdaGpio != pcfSclGpio, "I2C SDA/SCL conflict");
}

