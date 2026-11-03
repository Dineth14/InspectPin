# Rev E corrected schematic specification

This is the net-level change specification to apply to the missing Rev E KiCad
source. It is not a substitute schematic.

## Sheet: power and battery

- Delete MAX17043/MAX17048, their decoupling, pull-ups and software-only nets.
- Retain XIAO USB-C/VBAT charging and connect only a protected 3.7 V nominal,
  4.2 V maximum, 900 mAh single-cell Li-Po with verified polarity/connector.
- `VBAT -> R_BAT_TOP 100 kΩ 1% -> BAT_SENSE -> R_BAT_BOTTOM 100 kΩ 1% -> GND`.
- `C_BAT 100 nF X7R` from BAT_SENSE to GND, placed at XIAO D5/GPIO6.
- Label BAT_SENSE as an analog net; no PHOTO/wake/digital connection is allowed.
- Add TP_VBAT, TP_BAT_SENSE and TP_GND. Expected BAT_SENSE is 1.60–2.10 V for
  a 3.20–4.20 V cell before calibration.

## Sheet: PCF8574 and controls

- PCF8574 at 3.3 V; A2:A0 low gives address 0x20. Add 100 nF at VDD.
- SDA to GPIO43 and SCL to GPIO44; each has 4.7 kΩ to 3.3 V. Standard mode
  100 kHz until measured bus capacitance allows otherwise.
- INT is open-drain to D4/GPIO5 with 10 kΩ to 3.3 V and TP_PCF_INT.
- PHOTO: P3 with 10 kΩ to 3.3 V and normally-open switch to GND.
- ASK: D2/GPIO3 with 10 kΩ to 3.3 V and normally-open switch to GND; label the
  strap warning on schematic and assembly drawing.
- No dedicated power button; P2 remains spare.
- Since PCF ports power up HIGH, P0/P1 pass through a dual 3.3 V inverter with
  input pull-ups so inverter outputs default LOW. Inverter outputs drive the
  existing flashlight transistor input and vibration module IN respectively.
  Verify that LOW means both loads are OFF.

## Sheet: charger-status indicator

- High-impedance sense of the XIAO SGM40567 `nCHG`/charge LED cathode node only.
- VBUS-powered low-power decoder generates exactly 500 ms ON / 500 ms OFF while
  charging and steady ON after validated EOC; USB absent removes its power.
- One low-current red 0603 LED, initial resistor 6.8 kΩ (about 0.44 mA nominal).
- Decoder outputs to PCF P4/P5/P6 are open-drain and pulled up only to 3.3 V:
  `USB_PRESENT_N`, `CHARGE_FULL_N`, `CHARGE_VALID_N`. No 5 V may reach PCF pins.
- Fault remains unsupported unless a separate real fault signal is added.

## Preserved sheets/nets

Do not alter the XIAO Sense camera, microphone or SD connector nets, the tested
MAX98357A GPIO1/2/4 interface, speaker differential connection, or approved
OV3660 profile. Verify MAX98357A and vibration-module supply availability on
battery; XIAO 5 V/VBUS is not assumed present without USB.

