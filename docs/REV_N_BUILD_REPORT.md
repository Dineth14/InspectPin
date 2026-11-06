# Rev N reproducible build report

Build date: 2026-11-05.

## Pinned toolchain

- Arduino CLI 1.2.0
- Espressif Arduino core `esp32:esp32` 3.3.12
- Board: `XIAO_ESP32S3`
- Options: OPI PSRAM, hardware USB CDC, CDC on boot, 8 MB flash, default 8 MB partition scheme
- Application flag: `-DIP_USE_REV_N_CONFIG`

Run `manufacturing/build_revn.ps1`. It refuses a different ESP32 core version, compiles both sketches, copies merged images and component images, and writes SHA-256 hashes.

## Actual compile results

| Target | Result | Flash usage | Static RAM |
|---|---|---:|---:|
| Rev N application | PASS | 1,133,758 bytes (33%) | 60,072 bytes (18%) |
| Rev N factory test | PASS | 486,643 bytes (14%) | 35,208 bytes (10%) |

The merged images are both 8,388,608 bytes. SHA-256: application `d006de6c71a579b68feef1ecdf201cb22ac6feafe9229993af9cb1ca8c24065b`; factory `bbea7740f9b067a4835041978448b2db99c95b7f8640d38c3c314ff75be1495a`. The complete component hashes are in `manufacturing/output/SHA256SUMS.txt`.

## Verification run

- Python/backend/factory-host tests: 153 passed.
- Native C++ state and power policy executables: both compiled with `-Wall -Wextra -Werror` and exited successfully.
- Web: 3 Vitest tests passed; TypeScript/Vite production build passed.
- Ruff: passed for backend and manufacturing Python.
- Documentation link check: 44 Markdown files checked, zero missing local targets at the time of the run.
- Flutter tests: not run because `flutter` is not installed on this workstation.
- KiCad ERC/DRC: not rerun because `kicad-cli` is not installed on this workstation.
- Physical Rev N FCT: not run; procedures are supplied and every hardware-dependent result remains unverified/BLOCKED.

