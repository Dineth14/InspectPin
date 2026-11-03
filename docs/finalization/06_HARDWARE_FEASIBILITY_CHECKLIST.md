# Hardware feasibility checklist

| Item | Purpose / electrical requirement | Proposed connection | Need |
|---|---|---|---|
| XIAO ESP32-S3 Sense + OV3660/Sense board | Controller, PSRAM, mic, camera, SD | Existing official camera/mic/SD nets | Mandatory, present |
| ASK/VOICE switch | Voice and candidate wake | D2/GPIO3 to GND; release during reset because strap pin | Mandatory, present but strap risk |
| PHOTO switch | Photo and candidate wake through expander INT | PCF8574 P3 to GND; INT to GPIO5 | Mandatory; verify PCF remains powered |
| Li-Po with protection | Portable power | BAT pads, correct polarity, suitable protected cell | Mandatory product; validate capacity/current |
| 100 kΩ + 100 kΩ 1% divider, 100 nF | Battery voltage estimate | BAT→100k→GPIO6→100k→GND; capacitor midpoint→GND | Mandatory; calibration/drain/back-power unverified |
| Optional divider disconnect FET | Reduce leakage/back-power | High-side/low-side topology reviewed for ADC safety | Optional |
| MAX98357A | I²S speaker amplifier | BCLK GPIO1, LRC GPIO2, DIN GPIO4, common GND, verified supply | Present; battery supply unresolved |
| 8 Ω speaker with adequate rating | Spoken output | Across SPK+ and SPK− only | Present; 0.5 W unit needs power/distortion test |
| White LED + existing transistor driver | Illumination | PCF P0 through fail-safe inverter to driver | Retain; verify 20mA/current/startup off |
| Complete vibration module | Haptic feedback | PCF P1 through fail-safe inverter to module IN | Retain; verify VCC/current/input/startup off |
| LRA + haptic driver | Higher-quality haptics | Dedicated driver over available bus/pins after conflict audit | Alternative to ERM |
| VBUS/charger-status sensing | Firmware charging indication | Additional protected VBUS divider and/or buffered/tapped CHG net after schematic/revision review | Optional; required for firmware-readable charging |
| VBUS-powered charge-status decoder | Convert SGM40567 native pulses/EOC interval into exact requested LED states without waking ESP32 | High-impedance `nCHG` tap, VBUS supply, protected one-wire/digital link to ESP32 | Mandatory for CHG-004/005 |
| One low-current red SMD LED + 6.8 kΩ initial resistor | 1 Hz charge blink, steady full, off without USB | VBUS→resistor→LED→decoder sink output | Mandatory; calculate again for selected LED |
| Logic-level translator/protection | Protect status inputs if rail exceeds GPIO | Divider/buffer/clamps calculated for worst case | As required |
| Bulk/local decoupling | Prevent audio/motor/LED resets and mic noise | At amp/drivers; values based on load/transients | Mandatory final hardware |
| External antenna | Reliable Wi-Fi/BLE | XIAO U.FL antenna fitted correctly | Present/mandatory for intended RF setup |
| High-endurance microSD | Media/video writes | Sense slot; FAT compatibility and speed tested | Mandatory video |

## Pin conflict decision

| Function | GPIO | Finding |
|---|---:|---|
| MAX98357 BCLK/LRC/DIN | 1/2/4 | Existing tested allocation; RTC-capable pins consumed. |
| Speech button | 3 | D2/ADC1_CH2/RTC; **strapping pin**. Must be released at reset and tested. |
| PCF8574 INT / wake | 5 | D4/RTC GPIO; active-low open drain; PHOTO input change can wake. |
| Battery ADC | 6 | D5/ADC1_CH5/RTC; analog-only in reconciled product. |
| SD | 7/8/9/21 | Existing official Sense allocation; GPIO21 also board LED. |
| Camera | 10–18,38–40,47,48 | Reserved by Sense camera. |
| PDM mic | 41/42 | Reserved by Sense microphone; not ADC-capable on this board use. |
| PCF8574 SDA/SCL | 43/44 | D6/D7; use USB CDC instead of UART0; controls/buttons move through expander. |

## Power and charging findings

Seeed documents onboard single-cell charging and a red hardware charge indicator. The v1.3 schematic identifies SGM40567 and a nominal charge-current network around 110 mA. Confirm the actual board revision and resistor before relying on that value. Its `nCHG` node is observable at the onboard LED network, but it provides pulsed charging and only a 51.2-second continuous completion indication before high impedance. The separate decoder in `09_SINGLE_LED_CHARGE_INDICATOR.md` is required for the exact external LED behavior and mobile-readable state. The 5 V pin is USB-derived and has no voltage during battery-only operation, so a 5 V MAX98357 supply requires a verified boost/power architecture or operation at a supported lower amplifier rail.

Required measurements: USB/battery rail voltage at idle and peak playback; total active/record/photo/video/sleep current; charger current and temperature; battery polarity/protection; brownout margin; LED/motor inrush; amplifier/speaker RMS using safe differential measurement; RF and microphone noise with loads switching.

## Driver acceptance

No light or haptic feature may be enabled until schematic, part numbers, load ratings, GPIO-off behavior, gate/base current, flyback/current limiting, thermal test, and power-cycle test are recorded. Charging UI must show `unknown` unless the optional sensing circuit has a tested truth table for USB absent, charging, full, battery absent, and fault where detectable.

