# Rev E electrical and firmware verification procedure

Do not fabricate or enable `config.rev_e.example.h` until sections 1–3 pass.
Record instrument model/range, board revision, ambient temperature, supply,
firmware commit, raw readings and photos. Blank evidence is a pending test, not a pass.

## 1. Schematic/ERC review

1. Open the actual Rev E KiCad project and apply `REV_E_SCHEMATIC_SPEC.md`.
2. Confirm MAX17043/MAX17048 and associated dependencies are absent.
3. Cross-probe every XIAO, PCF, inverter, battery, LED, module and test-pad pin.
4. Run KiCad ERC. Resolve errors; document intentional warnings with reviewer rationale.
5. Run schematic/PCB consistency and DRC, but do not generate fabrication output.

## 2. Unpowered continuity and resistance

- Confirm no continuity from BAT_SENSE/GPIO6 to PHOTO, PCF INT or other digital net.
- Measure approximately 100 kΩ from VBAT to BAT_SENSE, 100 kΩ BAT_SENSE to GND,
  and approximately 200 kΩ VBAT to GND after capacitor settles.
- Confirm ASK→GPIO3, PHOTO→PCF P3, PCF INT→GPIO5, SDA→GPIO43, SCL→GPIO44.
- Confirm PCF P0/P1 inverter outputs are LOW when PCF inputs are HIGH/unpowered.
- Confirm speaker is only across SPK+/SPK− and battery polarity is correct.

## 3. Current-limited first power

Use a current-limited supply and no Li-Po initially. Verify 3.3 V, I²C pull-ups,
BAT_SENSE and load-driver OFF states. Confirm PCF address 0x20. Exercise P0/P1
with loads disconnected before connecting the flashlight and vibration module.

## 4. Battery ADC calibration

Apply safe simulated cell voltages at 3.20, 3.40, 3.70, 4.00 and 4.20 V.
At each point record supply/DMM cell voltage, BAT_SENSE, raw millivolts, filtered
voltage, estimated percentage and uncertainty. Expected BAT_SENSE is one half
the cell voltage. Calculate one calibration multiplier, persist it, then repeat.
Pass when all corrected points fall inside the documented uncertainty and no
sample is invalid or above ADC constraints. Repeat idle, Wi-Fi, camera and audio
load points to quantify sag; do not tune percentage linearly to those five points.

## 5. Divider standby and back-power

At 4.2 V, theoretical divider current is 21 µA. Measure actual battery current
with the divider fitted and removed, using an instrument suitable for µA. Record
the delta and decide the allowed standby budget. If testing a genuinely
unpowered ESP/load-switched rail, apply VBAT through the divider and measure
GPIO6, 3V3 and rail current for injection/back-power. Do not perform this by
shorting rails or defeating battery protection. If injection is unacceptable,
add a reviewed analog switch or gated divider and repeat ERC/tests.

## 6. Buttons and automatic power saving

Verify 50 resets with ASK released and 10 held-at-reset trials; no boot-mode or
false command is allowed. Verify 100 ASK and 100 PHOTO presses including bounce,
simultaneous presses and holds. With a short test timeout, confirm active media
work defers sleep. Measure ready and automatic light-sleep current. Wake 50 times
with ASK and 50 with PHOTO through PCF INT. Only then trial deep sleep; require
the same cycles, PCF retention, INT clearing and no wake loop. If deep sleep
fails, ship light sleep/idle saving rather than adding a third button.

## 7. Charging and one LED

With a protected 900 mAh cell and the exact XIAO revision, record charger current,
cell/board temperature and time. Probe VBUS, `nCHG`, decoder inputs/outputs and
LED current. Require 500 ms ON/500 ms OFF for at least 20 charging cycles,
steady ON for 10 minutes after EOC (including native `nCHG` high-impedance), and
OFF with USB removed. Firmware/mobile must match decoded state while awake and
show unknown/stale when unavailable. Fault stays unsupported.

## 8. Preserved-function regression

Run SD self-test, 10 optimized SVGA photos, microphone WAV capture, MAX98357A
playback, PCF PHOTO/ASK, flashlight current/exposure, vibration current/noise,
Wi-Fi/backend voice, visual Q&A and the existing AVI test. Record heap/PSRAM,
hashes and brownout/reset behavior. A compile is not a physical pass.

