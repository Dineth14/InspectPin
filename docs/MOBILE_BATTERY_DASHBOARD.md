# Mobile battery dashboard contract

The Android-first Flutter source under `mobile_app/` now has a typed battery
model and accessible dashboard card. It displays calibrated voltage with
uncertainty, non-linear estimated percentage, sample age, low/critical warning,
and independently valid charger state. A 100% voltage estimate cannot display
“charge complete” unless `charge_valid=true` came from the hardware decoder.

Expected device status JSON fragment:

```json
{
  "battery": {
    "voltage_v": 3.78,
    "estimated_percent": 66,
    "uncertainty_v": 0.08,
    "valid": true,
    "low": false,
    "critical": false,
    "sample_age_ms": 250,
    "charge_state": "unknown",
    "charge_valid": false
  }
}
```

The live authenticated device-status API is not implemented yet, and Flutter is
not installed in the current environment, so source creation is not a mobile
build pass. Run `flutter format .`, `flutter analyze`, `flutter test`, and
`flutter build apk --debug` after installing the pinned-compatible Flutter SDK.

