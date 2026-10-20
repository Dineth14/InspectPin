# OV3660 camera optimization

## Approved profile and evidence

InspectPin uses `INSPECTPIN_CAMERA_PROFILE_OPTIMIZED` by default. It targets readable component labels and nameplates at SVGA rather than CameraWebServer streaming speed. ESP32 Arduino core 3.3.12 exposes the configured fields through `sensor_t::status`, so the firmware checks setter return codes and readbacks before accepting a capture.

The original tuned CameraWebServer `/status` JSON was not retained in this repository. Values that cannot be recovered exactly are identified instead of being presented as measured values.

| Control | Firmware value | Reference status |
|---|---:|---|
| Sensor | OV3660 PID `0x3660` | Required and verified at runtime |
| XCLK | 20,000,000 Hz | Exact task value and CameraWebServer initialization |
| Pixel format | JPEG | Exact required value |
| Final frame size | SVGA, 800 x 600 | Approved final inference resolution |
| JPEG quality | 12 | Requested approximate value; provisional until original `/status` is recovered |
| Brightness | +1 | Requested value and official OV3660 CameraWebServer startup value |
| Contrast | 0 | Requested value; provisional until original `/status` is recovered |
| Saturation | -2 | Requested range was -1 to -2; provisional choice supported by official OV3660 startup code |
| Sharpness | +1 | Requested approximate value; provisional until original `/status` is recovered |
| De-noise | 5 | Requested approximate value; provisional until original `/status` is recovered |
| Exposure level | 0 | Requested value; provisional until original `/status` is recovered |
| Gain ceiling | Preserve initialized sensor register state | Exact manually tuned number is unknown; the observed driver status was raw value 248 and is not claimed to be the lost tuned value or an enum |
| AWB / AWB gain | 1 / 1 | Required enabled values |
| White-balance mode | 0, auto | Manual preset disabled |
| AEC / night mode (`aec2`) | 1 / 0 | Auto exposure enabled; installed UI maps Night Mode to `aec2` |
| AGC / raw gamma / lens correction | 1 / 1 / 1 | Enabled; lens correction is optional only if a future driver omits it |
| Advanced AWB | `dcw=1` | This is the installed CameraWebServer OV3660 UI mapping, not a name-based guess |
| Vertical flip | 1 | Official CameraWebServer OV3660 correction for the initially inverted image |
| Special effect | 0 | Normal image |

The installed web UI labels `awb_gain` as “Manual AWB,” while its mode selector is `wb_mode`. The task requires AWB gain enabled and manual white-balance selection disabled, so InspectPin sets `awb_gain=1` and keeps `wb_mode=0` (auto). Serial output prints both fields separately.

The CameraWebServer sketch begins with UXGA to allocate buffers, then changes the live sensor to QVGA for streaming. InspectPin does neither transition: its initialized and final sensor size is SVGA. The screenshot’s UXGA selection therefore does not override the explicitly approved 800 x 600 inference resolution.

## Firmware behavior

`applyOptimizedCameraProfile(sensor_t *)` in `camera_manager.cpp` is the public optimized-profile entry point. `applyConfiguredCameraProfile()` selects the optimized profile by default and supports the explicit low-light experiment. Every image route calls `captureJpeg()`, including serial `c`, the D5 camera button, the single-button long gesture, and any future caller using the existing capture function.

For every capture the firmware:

1. Requires PSRAM and initializes the official XIAO ESP32-S3 Sense camera pins at 20 MHz, JPEG, SVGA.
2. Requires the detected PID to be OV3660.
3. Applies all settings, checks setter return codes, and compares `sensor_t::status` readbacks.
4. Prints the diagnostics and checks the profile again immediately before acquisition.
5. Enables optional illumination, waits 500 ms, and discards two warm-up frames for AWB/AEC settling.
6. Requires JPEG SOI/EOI markers, no more than 2 MiB, and exactly 800 x 600 dimensions.
7. Refuses to overwrite an existing path, writes the JPEG, reopens it, and verifies its stored byte count.
8. Returns every frame buffer, disables illumination, and deinitializes the camera.

An initialization, profile, warm-up, or frame error causes one complete deinitialization/reinitialization attempt. Reinitialization always reapplies the profile. An incomplete new SD file is removed, while earlier good files remain. `Store::newPath()` uses collision-checked random/time names under `/inspectpin`; this provides the same non-overwrite guarantee as sequential `/inspectpin_0001.jpg` names without a counter journal.

The upload code opens that stored JPEG and passes the `File` stream directly to `HTTPClient::sendRequest`. It does not create a second full-image buffer. The backend stores and hashes the exact received bytes. Any model-side transformation does not alter the original SD JPEG or server input file.

## Recover the exact CameraWebServer values

Flash CameraWebServer only when it is acceptable to replace the current InspectPin firmware, tune the controls, and save the status before leaving the page:

```powershell
$status = Invoke-RestMethod http://CAMERA_IP/status
$status | ConvertTo-Json -Depth 4 | Set-Content ov3660-tuned-status.json
```

Retain at least `quality`, `brightness`, `contrast`, `saturation`, `sharpness`, `wb_mode`, `awb`, `awb_gain`, `aec`, `aec2`, `ae_level`, `agc`, `gainceiling`, `raw_gma`, `lenc`, `dcw`, `vflip`, `xclk`, `pixformat`, and `framesize`. Copy only established values into `camera_profile.h` or private compile overrides. The OV3660 driver initializes `status.gainceiling` from the raw `0x3A18/0x3A19` register value but its setter accepts an enum, so an untouched status can be outside enum range 0..6. The connected sensor reported raw status 248. Do not translate that to “128x.” Set `IP_CAMERA_GAIN_CEILING` to 0..6 only if the retained tuned `/status` and matching driver behavior establish the intended value. The enum labels are 2x through 128x, but an [open Espressif driver issue](https://github.com/espressif/esp32-camera/issues/854) questions that OV3660 setter mapping; preserving the register state is safer until resolved.

## How the controls affect recognition

- Brightness and AE level shift the target image level. Excessive positive values wash out reflective labels.
- AEC selects exposure time and AGC selects sensor gain. Longer exposure can blur a handheld image; higher gain increases noise. Gain ceiling limits how far AGC may go.
- AWB corrects color cast. Let it settle after changing the scene or illumination.
- Contrast separates tones but can clip pale print or dark regions.
- Saturation affects color strength; reducing it can make colored sensor noise less distracting.
- Sharpness strengthens edges but can add halos around characters. De-noise suppresses grain but can erase fine print.
- Gamma changes midtone rendering. Lens correction compensates supported optical shading/distortion.
- JPEG quality uses the camera-driver convention: a lower number gives higher image quality and a larger file.

Focus, camera motion, viewing angle, reflections, and character pixel height usually matter more than another small slider change. Hold the camera square to the label, fill the frame, use diffuse light, and verify the saved JPEG on a computer before judging Qwen. If text is unreadable in the JPEG, the model must say it is unclear; recapture closer instead of trusting a guessed rating.

## Serial and fair comparison procedure

Open Serial Monitor at 115200 baud. Send `k` to initialize the camera, apply the selected profile, print every readback, and deinitialize without saving. A pass ends with `Optimized profile: APPLIED AND VERIFIED` and `Camera profile diagnostic PASS`. Unsupported, failed, and mismatched controls are printed explicitly.

Send `c` for a real image. Record the printed filename, byte count, dimensions, profile name, lighting, camera distance, angle, and target. Copy the JPEG from `/inspectpin` without editing it. For comparisons, keep the target, tripod position, crop, light, supply, and warm-up time unchanged. Compare original files at 100% zoom and use the same model prompt.

The optional `INSPECTPIN_CAMERA_PROFILE_LOW_LIGHT_TEST` is selected only by explicitly defining `IP_CAMERA_PROFILE` to that name. It keeps the image controls but uses AE level +1, a 1000 ms settle time, and four warm-up frames. Those values are experimental and have no claimed hardware result. Return to the optimized profile after comparison.

To explore UXGA later, make an experimental branch or private compile-time variant of the frame-size and dimension checks, label its images separately, and compare file size, reliability, latency, motion blur, and recognition. Keep the committed approved default at SVGA and never add CameraWebServer’s QVGA streaming downgrade.
