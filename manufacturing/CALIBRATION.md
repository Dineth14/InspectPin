# Rev N calibration

## INA219

The firmware uses a 0.1 ohm shunt and 100 uA/bit current LSB. From the TI equation, `CAL = 0.04096 / (current_LSB * Rshunt) = 4096`. This is a nominal calibration, not a substitute for production calibration.

At a minimum, record DMM and INA readings near 100 mA and 500 mA in both expected current directions. Calculate gain/offset only after shunt resistance and fixture lead error are characterized. Reject units whose calibrated error exceeds the product tolerance approved by engineering; the default factory firmware intentionally marks this step BLOCKED.

## NTC

The mathematical default is 10 kOhm at 25 C, Beta 3950, 10 kOhm pull-up to measured 3.3 V. Compare at ambient and one elevated safe temperature. Open and short states must be detected. Do not interpret this monitor as a charger cutoff.

## Audio, camera and light

Approve repeatable fixture limits only after a golden unit set is characterized. The firmware validates digital capture and file structure; audible quality, optical output, focus and nameplate readability require measured fixtures or an operator.

