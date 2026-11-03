# Single external charging LED decoder

The selected design and electrical calculations are normative in
[`docs/finalization/09_SINGLE_LED_CHARGE_INDICATOR.md`](../docs/finalization/09_SINGLE_LED_CHARGE_INDICATOR.md).
The stock SGM40567 `nCHG` waveform cannot directly provide the requested exact
500 ms/500 ms blink and persistent full indication. A VBUS-powered ATtiny202/
402-class decoder senses the charge LED cathode node through 10 kΩ plus a 1 MΩ
pull-up, drives one low-current red 0603 LED through an initial 6.8 kΩ resistor,
and latches full after sustained EOC-low evidence. Nominal LED current is about
0.44 mA; charging-blink average is about 0.22 mA.

`hardware/charge_decoder/charge_decoder_logic.h` is the independently testable
non-blocking control policy. Repeated approximately 160 ms low pulses select
CHARGING and generate exact 1 Hz/50% output. A continuous low longer than the
validated threshold selects and latches FULL while VBUS remains. USB absence
removes decoder power and LED output. The stock charger has no documented fault
signal, so fault indication remains unsupported.

The ESP32-side `ChargeStatus` interface deliberately returns `unknown`,
`valid=false`, and `source=unavailable` until a protected decoder status link
and dedicated pin are physically present. GPIO43/44 are already proposed for
light/haptic, so the link is a PCB pin-budget gate. Mobile software must display
unknown/stale rather than infer completion from voltage.

