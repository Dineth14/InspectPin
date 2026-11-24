# InspectPin AI evaluation build — 24 November 2026

## Laptop evaluation release

For Thursday's evaluation use [Start InspectPin and the local operator guide](LOCAL_EVALUATION.md). Public hosting is deferred. The evaluation firmware uses the manufactured single-layer profile. The local build uses 1,234,954 bytes of flash and 60,656 bytes of static RAM. The app binds login sessions to receiver origins, can verify a newer authenticated heartbeat, and exposes **Open inspection**, **Inspector note** and **Download PDF** in inspection lists. Flutter analysis passed, six Flutter tests passed, the Android debug APK and web client built, the React production bundle built, and 174 backend tests passed. See the [measured USB and operator results](PHYSICAL_ACCEPTANCE_TESTS.md#laptop-evaluation-rehearsal-24-november-2026) before treating any battery acceptance item as complete.

## Zero-cost cloud candidate

The separate Oracle deployment package adds operator-configured Groq and Gemini text/vision, optional Groq transcription and a free-plan model allowlist. The Android debug APK and Flutter web app built successfully. The backend passed 174 tests, Flutter analysis passed, all three Flutter tests passed, and Docker Compose and Caddy validated. An offline Linux AMD64 run synthesized and transcribed the reference question in 3.9 seconds. Public DNS, cloud-account entitlements, real provider inference and the battery/hotspot test need the operator's Oracle account and device. [Deployment guide](ZERO_COST_CLOUD.md)

The ARM64 cloud image also completed the offline speech loop with the original question correctly transcribed. The 168.2-second timing was measured under emulation. See the [ARM compatibility record](ZERO_COST_CLOUD.md#arm-compatibility) for the dependency pin and native A1 qualification.

## Final candidate rehearsal

Current results supersede the earlier numbers below. **169 backend tests, three Flutter tests, three React tests and both firmware host test programs passed.** Flutter analysis and Python lint passed. The manufactured single-layer sketch compiled at 1,227,010 bytes flash and 60,592 bytes static RAM. The candidate is in `.build/final-evaluation-20261124`; the application binary SHA-256 is `79105980854331a07d3592a0300e4ef2c6c913cadb7fc0f8e646e7864fae070f`.

| Measured path | Input and result | Measured interval |
|---|---|---|
| LAN receiver image job | Synthetic DEMO-123 nameplate. Qwen2.5-VL read **230 V** and Piper returned a canonical WAV. Job `d15df5c6c64e49bd8d59fa7e83684ed9`. | 13.62 s from request to downloaded speech. |
| LAN receiver voice job | A 2.85 s synthetic WAV asked “What voltage is printed on this label?” Whisper transcribed the question, Qwen answered **230 V** using the registered image, and Piper returned speech. Job `dc53def6564844749e0d42f9f99fb49a`. | 11.61 s from request to downloaded speech, including 0.69 s STT, 7.56 s vision and 3.31 s TTS. |
| Protected media | A full 60 s WAV survived upload and download byte-for-byte. A real archived AVI converted to a 74,004-byte MP4; all 51 frames decoded with no audio stream. | 0.11 s encode plus decode for this archived sample. |

The inference times are single software trials using the already-running receiver. Board capture, Wi-Fi from the wearable, and audible playback add time. `backend/scripts/live_rehearsal.py` can repeat the experiment against a running service. Per-call Ollama keep-alive defaults to zero to release model memory after each response. A host with sufficient memory can set `OLLAMA_KEEP_ALIVE_SECONDS` to trade memory for warm follow-ups.

The previous Docker CDN failure cleared on the hotspot. Docker 28.4.0 downloaded the base and built `inspectpin-hosted-evaluation` with its speech models (image ID `698b1605b742`). The LAN workspace has zero accounts with stored OpenAI or Anthropic credentials. No hosted service or cloud AI charge was initiated.

Linux image tests also passed with networking disabled. Under a 1.5 GiB container cap, Piper generated the question and Whisper recognized it in 3.21 s combined. A second container mounted the same test data, opened the saved inspection and verified the WAV checksum. Public-host persistence and device-to-Internet HTTPS remain separate acceptance checks.

The new media endpoint authorizes each original before serving a bounded, temporary MP4, including range requests. The Flutter and React players retain the original AVI download and GIF fallback. Recorded duration appears in both clients. The firmware suppresses network heartbeat requests during video, checks free SD capacity periodically, reports runtime memory during notes/clips and preserves a pre-existing destination on a name collision. Hosted provider dispatch pins restored workspace settings to the operator's model origin and restricts local routing to deployments configured to offer it.

**Recovery.** Windows detected the XIAO ESP32-S3 with 8 MiB flash and PSRAM on COM7. ESP ROM readback completed and the device verified the entire 8 MiB rollback image. The private recovery directory is `.backups/evaluation-before-flash-20261124-150133` and contains `config.local.h`, `rom-original.bin` and `flash.sha256`. Its verified SHA-256 is `da8963b340147370572b0357a3aaf3ac407b71d44441401636fd8da5f1b4feb3`. The installed and candidate partition tables matched. Previous Flutter web and Android builds were saved to `.backups/evaluation-clients-20261124-151048`. Keep these paths on the owner's machine.

See the [board installation and acceptance record](PHYSICAL_ACCEPTANCE_TESTS.md) and [hosted qualification instructions](CLOUD_DEPLOYMENT_GUIDE.md). The operator-provided loopback web address is the LAN demo's laptop frontend. Public deployment, provider credits, laptop-off independence and a witnessed full presentation remain open. Demonstrate functionality with the measured LAN workflow, use the original image and report to explain differentiation, show the real enclosure and manual for appearance/documentation, and rehearse the [five-minute sequence](EVALUATION_DEMO_PLAN.md) for presentation.

### Candidate file map

**Release copy.** The owner-only directory `.backups/evaluation-before-flash-20261124-150133/candidate` contains 52 checksum-verified artifact files, including the APK, Flutter web, React distribution, app binary, two backup clips and the two measured job records. Its `sha256.json` lists their digests. `receiver-and-instructions.zip` holds the receiver implementation and operating instructions. Private deployment configuration is preserved separately in the restricted parent directory. Final Android debug APK SHA-256: `9e0261fddc9bddd0037879fd79a89a2f91e41988256cf22efd109d373b58a33d`. The candidate awaits operator permission to replace the installed firmware. The known-working LAN image remains the evaluation fallback.

| Area | Files |
|---|---|
| Capture | `firmware/InspectPinAI/{app_state_machine,audio_recorder,video_recorder}.cpp` |
| Receiver | `backend/inspectpin/{ai_configuration,app,config,llm_providers,product_routes,recordings,video_playback,vision}.py`, `backend/.env.example`, `backend/scripts/live_rehearsal.py` |
| Tests | `backend/tests/test_ai_configuration.py`, `backend/tests/test_evaluation_release.py` |
| Flutter and Android | AI settings and inspection shell, product models, API client, Android/web evidence export modules, Android MainActivity |
| React | `web/src/{App.tsx,api.ts,types.ts,components/Recording.tsx}` |
| Operation | Release notes, hosted guide, physical acceptance, media architecture, user manual, evaluation demo plan |

### Earlier evaluation build

**Open the app on this laptop:** double-click `Open InspectPin.cmd` in the repository or open `http://127.0.0.1:5180` while the app server is running. The launcher serves the existing Flutter build on loopback. The receiver is a separate process. [Operating guide](USER_MANUAL.md)

## Release evidence

| Category | Evidence and scope |
|---|---|
| Verified on physical hardware | Operator confirmed battery-powered operation and model answers on the installed firmware. Earlier camera/voice evidence is in docs/evidence. |
| Verified through software testing | 166 backend tests passed, up from the 162-test baseline. The recording tests exercise authenticated upload, malformed files, idempotency, byte-exact download, cross-account denial, preview, inspection notes, PDF and offline policy. Three Flutter tests and three React tests passed. Flutter analysis and Python lint passed. |
| Compiled and awaiting physical validation | The XIAO single-layer sketch compiled, using 1,226,658 bytes of program storage and 60,584 bytes of static RAM. Android debug APK, Flutter JavaScript web build and React production build were generated. Independent note/video buttons, full-length playback, repeated captures and sleep/wake on the new build need a physical rehearsal. |
| Partially implemented or validated | Hosted Docker recipe, production authentication and hosted speech packaging are available. The local container build was blocked fetching the Python base image because Docker's registry CDN hostname could not resolve. A public backend, board-to-cloud TLS, paid model access and laptop-off operation are unverified. Automatic mode routes by input and the owner's configured models. |
| Deferred | Synchronized A/V, automatic provider failover, validated endurance and fleet-scale operation. Browser WebAssembly is limited by the secure-storage plugin; the built web app uses JavaScript. |
| Unsupported by manufactured PCB | Firmware battery voltage/percentage, charge state, flashlight and vibration controls. |

**Speech evidence.** A standalone local Piper/Whisper check recognized a synthesized question; the observed synthesis, model-load and transcription times were about 4.88, 3.78 and 0.78 seconds respectively. An isolated full-job retest encountered model allocation failures under memory pressure. A Windows CPU initialization fallback is included. No fresh end-to-end latency or physical playback measurement is asserted for this build. Repeat with `.\.venv\Scripts\python.exe backend\scripts\evaluation_voice_smoke.py` in a separate rehearsal with sufficient free memory. This test starts another receiver in-process and uses a temporary database.

**Laptop incident.** VS Code logged an out-of-memory renderer exit at 14:21 on 24 November. Windows logged resource-exhaustion events while local inference, the browser and Python consumed multiple gigabytes. During recovery the idle Android build daemons and unused Docker engine were stopped. The running receiver returned ready; the Flutter manifest, HTML, bootstrap, compiled application and local CanvasKit asset were served by the laptop. Keep development builds and independent model smoke tests separate from the live demonstration.

## Artifacts and commands

Run these from the repository root unless indicated. The original LAN firmware remains installed unless a technician explicitly uploads the new build.

| Deliverable | Location and use |
|---|---|
| Laptop app | `mobile_app/build/web/index.html`. Double-click `Open InspectPin.cmd`; to verify the server alone run `& '.\Open InspectPin.cmd' --no-browser` in PowerShell. |
| Android | `mobile_app/build/app/outputs/flutter-apk/app-debug.apk`. With the intended Android device authorized for USB debugging, run `& 'E:\InspectPinToolchain\android-sdk\platform-tools\adb.exe' install -r 'mobile_app/build/app/outputs/flutter-apk/app-debug.apk'`. Select the current receiver origin at sign-in. |
| React | `web/dist/index.html`. For a local preview, from `web` run `npm.cmd run preview` if available, or `npx.cmd --no-install vite preview --host 127.0.0.1`. The API must be reachable through the configured same-origin proxy. |
| Firmware | `.build/evaluation-firmware/InspectPinAI.ino.bin` plus bootloader/partition files in the same directory. Treat locally provisioned binaries as private. Compile flags and target are in the complete handoff. To upload the compiled directory, confirm the board's COM port and run `arduino-cli upload -p COMx --fqbn esp32:esp32:XIAO_ESP32S3 --input-dir .build/evaluation-firmware firmware/InspectPinAI` with that port. |
| Baseline recovery | Source baseline `099b5507`; local source snapshot `.build/evaluation-source-099b550.zip`. Restore private settings separately and select the single-layer target as documented. |

For a fresh Flutter web build, from `mobile_app` run `..\.tools\flutter\bin\flutter.bat build web --dart-define=INSPECTPIN_API_URL=http://127.0.0.1:5000`. For local service startup use `.\.venv\Scripts\python.exe backend\receiver.py` from the root with the private LAN settings. Start only one receiver on that port. For a real hosted instance, enrollment, backups and rollback follow the [cloud deployment guide](CLOUD_DEPLOYMENT_GUIDE.md).

## Engineering changes

* Firmware: button policy, app state machine, audio recorder/player, Wi-Fi and API client implement separate recordings, SD streaming/retry, amplifier volume restoration and TLS time synchronization.
* Backend: receiver, server configuration, AI configuration, job pipeline, product store/routes, device routes, recording decoder and tests implement bounded originals, receipt deduplication, notes/reports, authenticated preview, provider audit data and production credential handling.
* Clients: Flutter AI settings, device control, inspection screens, product models, API service and platform export modules; Android audio and file saving; React inspection and recording components. Browser evidence export uses package:web. GIF previews reuse Pillow; Linux hosted speech uses the project's existing AI dependencies.
* Operations: hosted Dockerfile, build context allowlist, local real-voice smoke script, laptop launcher and the evaluation documents linked below. Private credentials and the unsanitized working data are excluded from the handoff.

The next release gate is the [physical acceptance rehearsal](PHYSICAL_ACCEPTANCE_TESTS.md). For the presentation use the [demo sequence](EVALUATION_DEMO_PLAN.md), [specification](PRODUCT_SPECIFICATION.md), [competitor comparison](COMPETITIVE_ANALYSIS.md) and [professor questions](PROFESSOR_QA.md).
