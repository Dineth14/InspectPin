# Final verification matrix

Statuses begin as `planned` unless current source/evidence proves otherwise. Future Codex phases must replace placeholders with exact file/test/evidence links.

| ID | Implementation module | Automated check | Manual hardware/app test | Pass criterion / evidence |
|---|---|---|---|---|
| PWR-001 | PowerManager/state machine | power-state tests | measure normal/light/deep | labels correct; transition log/current sheet |
| PWR-002 | wake controller/GPIO6 | wake config contract | 50 wake/reset/held cycles | 50/50; serial video/current log |
| PWR-003 | idle policy/settings | timeout/defer tests | timeout/manual sleep | persisted and safe; transition log |
| PWR-004 | peripheral lifecycle | lifecycle mocks | rail/current by state | quiesce/resume; measurement table |
| PWR-005 | operation guard/storage | interruption simulation | reset during each write | prior files valid; hashes/files/logs |
| BTN-001 | ButtonManager/dispatcher | debounce/gesture tests | bounce/simultaneous/held | one intended command; serial/video |
| BTN-002 | pin configuration | pin contract | strap boot and wake | no boot fault; 50-cycle record |
| BAT-001 | BatteryMonitor | conversion tests | ≥5 multimeter points | documented error bounds; CSV |
| BAT-002 | filter/profile | noise/lookup/hysteresis tests | loaded/idle comparison | stable estimate; plots |
| BAT-003 | status schema/app | serialization/UI tests | compare device/app | exact acknowledged sample; screenshots/JSON |
| BAT-004 | power policy | threshold tests | controlled supply boundary | correct inhibit/finalize/sleep; video/log |
| CHG-001 | hardware docs | document/source check | USB charge/current/temp | safe behavior; measurement/photos |
| CHG-002 | status model | unknown-state tests | voltage-only scenario | never false charging claim; API capture |
| CHG-003 | optional sensor | truth-table tests | absent/charge/full/fault | matches verified circuit; schematic/log |
| CHG-004 | VBUS status decoder/one LED | decoder timing/state tests | charge/full/USB-off timing and current | 500/500 ms, steady ≥10 min, off; scope/video/current |
| CHG-005 | decoder link/charge status model | protocol/stale-state tests | deep sleep/off and mobile comparison | LED independent; app actual/stale truthful; traces |
| CHG-006 | capability/fault model | unsupported-state tests | inject fault only if hardware exists | no fabricated fault; rapid blink evidence if supported |
| CAM-001 | camera profile/manager | firmware contract tests | profile readback + 10 JPEGs | 800×600/profile verified; images/log |
| CAM-002 | storage/capture | unique-name/error tests | 10 captures/full SD | no overwrite; hashes/free-space |
| LGT-001 | LightController | safe-default/policy tests | power cycles/error/sleep | off in all safe states; measurements |
| LGT-002 | light command/PWM | clamp/state tests | brightness/exposure | actual state consistent; images/current |
| VID-001 | AviWriter/VideoRecorder | AVI parser tests | Windows/Android playback | valid silent AVI; file/hash/video |
| VID-002 | video profiles | validation/benchmark parser | fps/resolution runs | allowed set equals measured set; CSV |
| VID-003 | stop/finalizer | stop/idempotency tests | 30 button/mobile stops | 30 playable files; latency/logs |
| VID-004 | control policy | fallback tests | load/concurrency experiment | fallback always works; experimental report |
| MED-001 | MediaCatalogue/API | range/list/delete tests | large transfer/delete | bounded RAM/digest match; heap/log |
| MED-002 | SD fault handling | storage fault tests | full/remove/corrupt/power loss | no reset/overwrite; recovery artifacts |
| AUD-001 | recorder/player | WAV contract tests | speech record/play | valid/intelligible/no reset; WAV/video |
| AUD-002 | volume/speech text | clamp/pronunciation tests | value/symbol listening | bounded and understandable; WAV/notes |
| HAP-001 | driver abstraction/docs | startup-off test | electrical/power cycle | GPIO drives only driver; schematic/current |
| HAP-002 | pattern scheduler | timing/queue tests | identify all patterns | non-blocking/distinguishable; trace/video |
| VOC-001 | intent classifier/dispatcher | corpus + injection tests | spoken alias set | target precision/recall; corpus report |
| VOC-002 | parameter/confirmation | boundary tests | sleep/reset/delete | invalid/no-confirm causes no action; logs |
| VOC-003 | command taxonomy | routing tests | representative commands | correct typed route/response; transcript JSON |
| AI-001 | existing backend pipeline | full pytest/provider mocks | real Whisper/Ollama/Piper | completed jobs; job JSON/model versions |
| AI-002 | conversations/vision | ownership/stale tests | image + two follow-ups | grounded same JPEG; images/jobs/audio |
| AI-003 | config/security | secret scan/redaction tests | inspect device traffic | no provider key; scan/capture |
| NET-001 | BLE provisioner/Wi-Fi | protocol tests | router/hotspot/wrong password | recoverable authenticated provisioning; logs |
| NET-002 | NVS credentials | persistence/redaction tests | reboot/factory reset | persists then erases; serial capture |
| API-001 | versioned API contracts | schema/contract tests | cross-channel workflow | documented compatible responses; traces |
| API-002 | auth/pairing | negative/replay tests | wrong/expired credential | fail closed; test report |
| API-003 | command operations | idempotency/state tests | retry lost acknowledgment | one action/terminal result; trace |
| API-004 | streamed transfers | memory/size tests | largest files | stable heap/digest; plots/hashes |
| SEC-001 | threat model/trust reset | security lint/tests | reset/re-pair/LAN probe | documented limitations/fail closed; report |
| APP-001 | Flutter shell/build | format/analyze/test/build | clean Android install | launches; CI/APK hash |
| APP-002 | onboarding/connection | state/widget tests | permission/pair/reconnect | complete/recoverable; screen recording |
| APP-003 | dashboard | model/widget tests | compare live state | all fields match API; screenshots/JSON |
| APP-004 | controls | command UI tests | every control/conflict | acknowledged actual outcome; traces |
| APP-005 | media | repository/widget tests | large AVI/view/share/delete | bounded/recoverable; screen video/hash |
| APP-006 | conversation | job/state tests | text/image/voice history | correct jobs/audio/context; recording |
| APP-007 | settings | schema/migration tests | persist/unsupported values | validated acknowledged values; screenshots |
| APP-008 | provider admin | secure-storage/redaction | configure real backend | secrets stay server-side; scan/network trace |
| APP-009 | diagnostics | export/redaction tests | export after failures | complete and secret-free; bundle |
| APP-010 | iOS capability gate | platform tests if enabled | real iOS validation | only validated features claimed; report |
| REL-001 | recovery policies | fault-injection suite | network/model/reset faults | recovery/no silent loss; evidence archive |
| REL-002 | instrumentation | metrics parser | 100 cycles + long video | no unexplained reset/leak; plots/logs |
| DOC-001 | docs set | link/command checks | beginner/viva walkthrough | user completes setup/demo; review sheet |
| DOC-002 | traceability/status | ID coverage check | evidence audit | every ID linked or pending; signed matrix |

