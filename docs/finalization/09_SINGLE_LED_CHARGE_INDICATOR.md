# Single SMD charging-status indicator requirement

## Verified charger behavior

The inspected XIAO ESP32-S3/Sense v1.3 schematic uses an SGM40567-4.2 charger. Its `nCHG` output is connected to the onboard charge-LED network through a 10 kΩ path to VBUS. The [official SGM40567 datasheet](https://www.sg-micro.com/rect/assets/e95e555a-a8a2-4761-b86a-6554dff2d8ed/SGM40567.pdf) specifies:

- While charging, `nCHG` sinks current for about 160 ms in each 1280 ms period.
- At charge completion, `nCHG` remains continuously low for 40 periods, approximately 51.2 seconds.
- After that completion interval, `nCHG` becomes high impedance.
- No separate persistent “full” output or documented charging-fault pattern is provided.

Consequences: the native signal is useful and electrically accessible at the onboard charge-LED node, but it does not natively produce the requested 1 Hz/50% blink and cannot hold an LED on indefinitely after completion. Battery voltage must not be used to fill that gap.

## Selected architecture

Use a tiny VBUS-powered, ultra-low-power status decoder on the InspectPin PCB. An ATtiny202/402-class device is a reference choice, subject to sourcing and final electrical review. It observes `nCHG` through a high-impedance protected input and independently drives exactly one external low-current red SMD LED. It is powered only when USB VBUS exists, so the LED and decoder are off during battery-only operation and remain functional while the ESP32 is in deep sleep or disconnected by an optional load switch.

Reference circuit for schematic capture, not permission to route without review:

```text
XIAO VBUS (5 V) ----+---------------- status decoder VDD
                    +-- 100 nF ------- GND
                    +-- 6.8 kΩ --|>|--- decoder LED_SINK output
                                  red 0603 LED

XIAO nCHG/charge-LED cathode node -- 10 kΩ series -- decoder STATUS input
STATUS input ------------------------- 1 MΩ --------- VBUS

decoder STATUS_OUT/one-wire ---------- protected dedicated ESP32 GPIO
decoder UPDI/program pad -------------- test pad
grounds ------------------------------- common
```

The 1 MΩ pull-up bypasses the onboard LED path to give the high-impedance state a defined logic level while adding at most about 5 µA when `nCHG` is low. The decoder input is high impedance and must not exceed the charger’s guaranteed sink current or disturb its onboard indication. Validate actual high/low voltages on the exact board revision before freezing values.

For a red LED with nominal 2.0 V forward voltage at 5.0 V, 6.8 kΩ gives about `(5.0−2.0)/6800 = 0.44 mA`. At 5.25 V and a conservative 1.6 V forward voltage, current is about 0.54 mA. Final resistor selection must use the chosen LED’s datasheet, brightness test, VBUS tolerance, decoder pin limits, and PCB viewing conditions.

## Decoder behavior

Use a non-blocking timer state machine:

| State | Evidence | LED |
|---|---|---|
| USB absent | Decoder unpowered / verified VBUS absent | OFF |
| UNKNOWN/startup | VBUS present but no valid charger pattern yet | OFF |
| CHARGING | Repeated short `nCHG` low pulses consistent with charger timing | Exact 500 ms ON / 500 ms OFF |
| FULL | Continuous `nCHG` low longer than a validated threshold, representing the specified EOC interval | Continuously ON; latch while VBUS remains |
| FAULT | Only if a separately documented hardware signal/pattern exists | Distinct rapid blink |

After FULL, retain the state through the later high-impedance `nCHG` condition. A new valid charge-pulse sequence returns to CHARGING. Use startup blanking so stale retained state is never displayed before checking current `nCHG`. If reset/reconnect persistence is required, use EEPROM only on state transitions, test battery-removed behavior, and document the ambiguity. Never treat “no pulses” or a high battery voltage alone as FULL.

The SGM40567 documentation examined here does not define a charging-fault indication. Therefore rapid fault blink is **not available** from the stock XIAO charger. It may be enabled only after adding and validating a separate fault-capable charger monitor. Unknown/ambiguous status remains OFF and is reported as unknown.

## Mobile synchronization and pin-budget gate

The decoder must expose its decoded state to the ESP32 through a protected digital or one-wire interface when the ESP32 is awake. The current proposed GPIO budget already assigns GPIO43 to illumination and GPIO44 to haptics, so PCB design must resolve this conflict before layout. Acceptable options are a dedicated reallocated GPIO, a small bus/I/O expander, or a supervisor that also owns another low-speed output. Do not share a line unsafely or remove haptics silently.

Firmware reports `usb_present`, `charge_state` (`unknown`, `charging`, `full`, optional `fault`), `source=hardware_decoder`, and sample age. The mobile app displays exactly that acknowledged state. When the ESP32 is deeply asleep/off, the hardware LED still works but the app cannot receive live updates; it must show the last sample as stale/disconnected.

## BOM additions

| Ref | Part | Purpose |
|---|---|---|
| U_CHGSTAT | ATtiny202/402-class VBUS-capable low-power MCU or reviewed equivalent | Decode `nCHG`, generate exact pattern, latch full, report state |
| D_CHG | One low-current red 0603 SMD LED | Only added InspectPin PCB charging indicator |
| R_LED | 6.8 kΩ initial value, 1%, 0603 | Approximately 0.44 mA nominal LED current |
| R_IN | 10 kΩ, 0603 | Input/transient isolation |
| R_PULL | 1 MΩ, 0603 | Defined high state with negligible charger loading |
| C_DEC | 100 nF X7R, 0603 | Decoder decoupling |
| TP_UPDI, TP_NCHG, TP_VBUS, TP_GND | Test pads | Programming and validation |

## PCB and power-budget requirements

- Place `C_DEC` immediately at decoder VDD/GND and keep the `nCHG` sense trace away from camera clocks, I²S, the switch node, motor, and LED power wiring.
- Place `R_IN` next to the decoder input; provide test pads without long stubs on the charger node.
- Put the one visible LED at the enclosure light pipe/edge, mark polarity, and prevent its light from entering the OV3660 or misleading the camera illumination path.
- Route no external load current through the XIAO `nCHG` node. Only the high-impedance sense network connects there.
- Add UPDI/programming access, a firmware/version marking for the decoder, and production test pads for VBUS, `nCHG`, LED sink, status link, and ground.
- Decide and document how the XIAO onboard red LED is masked or treated as internal so the product presents one user-facing charging indicator.

At 5.0 V with the reference 6.8 kΩ/red LED, external LED current is approximately 0.44 mA steady and 0.22 mA average at 50% blink. Decoder supply current must come from its selected-part datasheet and be measured in UNKNOWN, CHARGING, and FULL. The circuit is VBUS-powered, so its battery-only contribution should be zero except any unintended path found during back-power testing. Add measured minimum/typical/maximum values to the final system power budget; do not use these calculated LED values as whole-circuit measurements.

If the existing XIAO onboard red charge LED remains visible, the assembled product physically has more than one charge-related LED. The enclosure/PCB specification must decide whether the onboard LED is masked, accepted as internal, or whether using only the onboard LED with its native nonconforming pattern is preferable. Do not remove or modify the XIAO LED network without Seeed schematic review and revalidation of `nCHG` loading.

## Physical acceptance

1. Measure VBUS, `nCHG`, decoder input, LED current, and charger current with USB absent, active charge, completion interval, post-51.2-second full state, battery absent, and reconnect.
2. Confirm 500±specified-tolerance ms ON and OFF for at least 20 cycles while charging.
3. Confirm steady LED for at least 10 minutes after completion, including after native `nCHG` becomes high impedance.
4. Confirm LED and decoder draw zero from the battery path, within instrument resolution, when USB is absent.
5. Confirm operation while ESP32 is awake, deep asleep, and—if fitted—load-switched off.
6. Confirm the onboard charger’s current, termination, and temperature are unchanged within measurement uncertainty after adding the high-impedance tap.
7. Confirm firmware/mobile state matches the decoder while connected; stale/disconnected UI is truthful during ESP off.
8. Do not claim fault indication unless an injected, independently detectable fault produces the documented rapid pattern.

