# Rev E ERC/electrical review report

Status: **BLOCKED — NOT RUN**

Reason: the Rev E KiCad project is absent and `kicad-cli` is unavailable. No
claim of zero ERC errors is possible.

Manual pre-ERC checks completed:

- GPIO6 battery ADC conflict identified; direct PHOTO removed from specification.
- No third power button; existing ASK and PCF INT are the only wake candidates.
- PCF ports default HIGH; fail-safe inversion is specified for both active-high loads.
- PCF inputs are not 5 V tolerant when supplied at 3.3 V; decoder outputs must
  be open-drain with 3.3 V pull-ups.
- MAX17043/48 are prohibited.
- Charger completion is not derived from battery voltage.
- Fixed camera, SD, mic and I²S allocations have no proposed overlap.

Required KiCad checks after source delivery: unconnected pins, power-input
drivers/PWR_FLAG use, duplicate net labels, I²C pull-ups, PCF address straps,
open-drain INT/status pull-ups, GPIO6 analog-only net, button pulls, inverter
truth table, LED polarity/current, module supply pins, battery polarity, test
points, and all footprint/pin-number mappings. Archive the real ERC output here.

