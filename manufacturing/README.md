# InspectPin Rev N firmware and FCT package

Start with `FLASHING.md`, then `FIXTURE_WIRING.md`, `CALIBRATION.md`, `EXPECTED_RESULTS.md` and `OPERATOR_PROCEDURE.md` in that order.

`output/inspectpin_revn_factory.bin` and `output/inspectpin_revn_application.bin` are merged images flashed at `0x0`. `output/SHA256SUMS.txt` is authoritative. The factory test needs no Wi-Fi or AI backend.

The optional charger/full test is BLOCKED in the released build because the normal XIAO pins do not expose NCHG. Do not change that result based on cell voltage.

