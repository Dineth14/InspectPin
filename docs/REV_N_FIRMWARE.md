# Rev N application firmware

The application target is `firmware/InspectPinAI`, compiled with `IP_USE_REV_N_CONFIG`. `config.revn.example.h` is the Rev N build profile and intentionally contains no credentials.

## Workflows

- PHOTO reads PCF8574 P0, validates the NTC, enables the GPIO4 flashlight only around capture, captures an 800x600 JPEG, writes a unique SD file, uploads it, retains image context and plays returned WAV audio.
- ASK reads PCF8574 P1, validates the NTC, records approximately five seconds of PCM16 audio, writes a WAV, uploads it with the current image context and plays returned audio.
- Failed/offline inputs remain on SD and can be retried. Bounded buffers and returned camera frame buffers avoid copying entire media files into another application buffer.
- INA219 supplies voltage/current/power telemetry. Battery percentage remains a calibrated voltage-curve estimate.
- The task watchdog is configured for 30 seconds, longer than the designed bounded camera/SD/HTTP calls. A persistent blocked operation causes a panic/reset.

## Configuration before flashing

Copy the example to an untracked local configuration only when credentials are needed, or supply build flags/secrets without committing them. Set the Wi-Fi SSID, password and laptop backend URL. The laptop address must be reachable from the same network; `127.0.0.1` points to the ESP32 itself and is invalid.

For charger truth, leave `IP_NCHG_AVAILABLE=false` unless an actual XIAO NCHG tap is inspected and electrically verified. With the default, USB insertion is shown but the firmware reports charge completion as unknown.

## Camera compatibility

The approved application setting is OV3660, 20 MHz XCLK, JPEG, SVGA, quality 12, brightness +1, contrast 0, saturation -2, sharpness +1 and denoise 5. The exact captured unit previously reported PID `0x3660`. Seeed may supply an OV5640 on newer Sense revisions; do not approve it merely because it initializes. Capture its PID in FCT and validate a separate profile before release.

## Backend

`backend/receiver.py` runs the modular Flask service. The base dependencies are pinned in `backend/requirements.txt`; optional local AI dependencies are in `backend/requirements-ai.txt`. Deterministic mock provider settings permit an end-to-end interface test without a GPU. Actual faster-whisper, Qwen2.5-VL/Ollama and Piper testing still depends on locally installed model files.

