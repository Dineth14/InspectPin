# InspectPin pin and electrical conflict matrix — Phase 0

This is a design decision record, not proof of assembled hardware.

| Board label | GPIO | Current source use | Proposed final use | RTC/deep wake | Conflicts and decision |
|---|---:|---|---|---|---|
| D0 | 1 | MAX98357 BCLK | retain | Yes | Consumed by tested audio; do not reuse. |
| D1 | 2 | MAX98357 LRC/WS | retain | Yes | Consumed by tested audio; do not reuse. |
| D2 | 3 | Voice button | Speech/command; long idle photo | Yes | **Strapping pin.** Switch to GND must remain released during reset; physical boot test mandatory. |
| D3 | 4 | MAX98357 DIN | retain | Yes | Consumed by tested audio. |
| D4 | 5 | Optional battery ADC | Battery divider midpoint | Yes | ADC1_CH4; cannot also carry I²C/status. Divider/back-power/calibration review required. |
| D5 | 6 | Current camera button | Power/wake button | Yes | Preferred non-strap wake. Camera moves to D2 long press/voice/mobile. Requires rewiring. |
| D6 | 43 | Optional light | MOSFET light control | No | UART0 TX alternate. Use USB CDC; never direct LED current. |
| D7 | 44 | Optional haptic | Haptic-driver control | No | UART0 RX alternate. Conflicts with charge-decoder status-link need. |
| D8 | 7 | SD SCK | retain | Yes | Official Sense SD; unavailable. |
| D9 | 8 | SD MISO | retain | Yes | Official Sense SD; unavailable. |
| D10 | 9 | SD MOSI | retain | Yes | Official Sense SD; unavailable. |
| onboard | 21 | SD CS / user LED net | retain SD CS | Yes | Do not blink onboard user LED while SD active. |
| expansion | 41 | PDM DATA | retain | No | Sense microphone; Seeed warns not ADC-capable here. |
| expansion | 42 | PDM CLK | retain | No | Sense microphone; unavailable. |
| camera | 10–18, 38–40, 47–48 | OV3660 DVP/SCCB | retain | Mixed | Reserved by official Sense camera wiring. |
| USB | 19/20 | Native USB/JTAG | retain | Yes | Do not repurpose; serial/programming diagnostics. |
| boot | 0 | BOOT | retain | Yes | Strap/boot control; unavailable to product controls. |

## Unresolved charge-status link

The VBUS-powered `nCHG` decoder needs to expose decoded CHARGING/FULL/UNKNOWN status to the ESP32. No uncommitted header GPIO remains under the proposed allocation. Before schematic freeze, choose and test one:

1. Reallocate GPIO44 from haptic and move haptic control to a reviewed auxiliary supervisor/expander.
2. Add a low-power bus/I/O expander with a conflict-free, electrically valid bus allocation.
3. Revise another optional feature/pin after user approval.

Do not electrically time-share an output driver and status input without a reviewed isolation circuit and boot/sleep truth table. Until resolved, firmware/mobile charge state remains `unknown`; the independent hardware LED may still operate.

## Fixed Sense nets

- Microphone: GPIO42 CLK, GPIO41 DATA.
- SD: GPIO21 CS, GPIO7 SCK, GPIO8 MISO, GPIO9 MOSI.
- Camera: GPIO10 XCLK; GPIO11/12/14–18 data; GPIO13 PCLK; GPIO38 VSYNC; GPIO39 SCL; GPIO40 SDA; GPIO47 HREF; GPIO48 data.

## Power and load constraints

- XIAO 5 V is USB-derived and absent in battery-only use. Verify the MAX98357 supply and any boost architecture.
- GPIO43/44 drive only MOSFET/transistor/driver inputs with defined pull-downs.
- The 47 kΩ/47 kΩ divider produces about 2.1 V at a 4.2 V cell and draws about 44.7 µA continuously unless switched.
- The charge LED decoder is powered from VBUS, senses `nCHG` at high impedance, and must not back-power the ESP32 or battery rail.
- Motor/LED/amplifier transient current, decoupling, ground return, microphone noise, and brownout require measurements.

## Official references

- Seeed XIAO ESP32-S3 pin multiplexing: https://wiki.seeedstudio.com/xiao_esp32s3_pin_multiplexing/
- Seeed XIAO ESP32-S3 schematic: https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/XIAO_ESP32S3_V1.3_SCH_260115.pdf
- Espressif ESP32-S3 GPIO/RTC: https://docs.espressif.com/projects/esp-idf/en/v5.1/esp32s3/api-reference/peripherals/gpio.html
- Espressif sleep modes: https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-reference/system/sleep_modes.html
- SGM40567 status behavior: https://www.sg-micro.com/rect/assets/e95e555a-a8a2-4761-b86a-6554dff2d8ed/SGM40567.pdf

