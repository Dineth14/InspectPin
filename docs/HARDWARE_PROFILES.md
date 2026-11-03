# Hardware profiles

## `xiao_esp32s3_sense_dev`

This is the verified development target. Camera, SD and PDM pins are fixed by
the XIAO Sense expansion hardware; MAX98357A uses D0/D1/D3. Historical bench
PHOTO/ASK wiring remains the default configuration so an existing prototype is
not silently rewired.

## `inspectpin_rev_e_candidate`

Enabled by `IP_USE_REV_E_CANDIDATE_CONFIG`. ASK is D2/GPIO3, PHOTO is PCF8574
P3, and the 100 kΩ/100 kΩ/100 nF battery divider is D5/GPIO6. PCF8574 and the
charge decoder are capability-gated. See the
[Rev E reconciliation](../hardware/REV_E_RECONCILIATION_REPORT.md).

The master prompt's `inspectpin_integrated_rev_h` is not assigned fictional
GPIOs. It remains a future alias only after an approved schematic and pin review.
MAX17043/MAX17048 are prohibited by the later final hardware decision.
