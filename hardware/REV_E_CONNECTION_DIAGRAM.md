# Rev E connection diagram

```text
Protected 1S Li-Po 900 mAh
  + -> XIAO BAT/VBAT
  + -> 100k -> BAT_SENSE -> 100k -> GND
                       +-> 100nF -> GND
                       +-> XIAO D5 / GPIO6 ADC

XIAO D0/GPIO1 -> MAX98357A BCLK
XIAO D1/GPIO2 -> MAX98357A LRC/WS
XIAO D3/GPIO4 -> MAX98357A DIN
XIAO D2/GPIO3 -> ASK normally-open switch -> GND

XIAO D6/GPIO43 <-> PCF8574 SDA -- 4.7k -> 3V3
XIAO D7/GPIO44  -> PCF8574 SCL -- 4.7k -> 3V3
XIAO D4/GPIO5  <- PCF8574 INT -- 10k -> 3V3

PCF P0 -> inverter -> existing flashlight transistor control (default OFF)
PCF P1 -> inverter -> vibration module IN (default OFF)
PCF P2 -> spare
PCF P3 -> PHOTO normally-open switch -> GND; 10k -> 3V3
PCF P4 <- charger decoder USB_PRESENT_N
PCF P5 <- charger decoder CHARGE_FULL_N
PCF P6 <- charger decoder CHARGE_VALID_N
PCF P7 -> spare/test pad

XIAO VBUS -> onboard SGM40567 charger
XIAO nCHG node -> high-impedance VBUS-powered decoder
decoder -> 6.8k -> one red SMD LED

Sense internal: camera unchanged; PDM GPIO42/41; SD GPIO21/7/8/9
```

All grounds are common, but route LED, motor and amplifier return currents away
from BAT_SENSE, microphone and camera references. Do not connect the speaker to
ground; use MAX98357A SPK+ and SPK− only.

