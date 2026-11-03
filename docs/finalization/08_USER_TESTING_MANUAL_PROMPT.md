# Copy-ready prompt for the complete user testing manual

```text
Work in E:\University Files\CS2\EE356\InspectPin after implementation Phases 0–9. Create or fully update docs/FIRST_TIME_SETUP.md as the authoritative beginner operating and testing manual. Inspect actual source, configuration names, API routes, Flutter package, installed Arduino FQBN, and scripts before writing. Do not copy stale commands or invent test results.

The manual must take a new Windows user from an unconfigured machine to a verified InspectPin interaction. Include prerequisites, exact download/install versions or supported ranges, repository setup, Python venv, locked dependencies, Ollama/Whisper/Piper/Qwen model setup, Arduino CLI/IDE board core/libraries, Flutter/Android SDK setup, and physical safety inspection.

Provide a final wiring table and diagrams for the exact accepted hardware: XIAO/Sense, MAX98357A/speaker, power/wake and speech buttons, battery divider, optional verified charge sensing, LED MOSFET/current control, and haptic driver/flyback. Clearly mark optional/unbuilt circuits. State that GPIO3 is a strap pin, the 5 V pin is unavailable from battery alone, motors/LED loads cannot be driven directly, and charging status may be unknown.

Give exact procedures and expected serial/app/API observations for:
1. Flashing firmware and selecting config without exposing secrets.
2. Starting/checking Ollama and the backend, Windows firewall/LAN binding, and changing hotspot IPs.
3. Building/installing the Android app.
4. Pairing/provisioning through BLE, selecting 2.4 GHz Wi-Fi/hotspot, wrong-password recovery, reconnect, and trust reset.
5. Verifying SD, microphone, speaker, camera profile, Wi-Fi, backend, battery, light, haptic, sleep/wake, versions, memory, and free storage.
6. Voice-only AI interaction and interpreting record/upload/job/download/playback states.
7. Photo capture, image registration, visual question, nameplate reading, follow-ups, context clear/expiry, and uncertainty.
8. Starting/stopping silent video by button/app, checking recording status, safe finalization, browsing/downloading/playing/sharing/deleting media, and recovering incomplete/full-SD cases.
9. Flashlight/haptic controls, timeouts, low-battery restrictions, and actual-state acknowledgments.
10. Battery voltage/estimated percentage calibration with a multimeter, uncertainty, low/critical behavior, charging LED versus firmware-readable status.
11. Light/deep sleep, manual/idle sleep, physical wake, busy-operation deferral, and the distinction from true power-off.
12. Mobile AI text/voice/image conversation, provider selection, model capability, audio controls, and secure backend configuration.

For every procedure include prerequisites, numbered actions, expected result, pass/fail criteria, evidence to save, and a troubleshooting branch. Add a command reference for firmware serial, device API, backend PowerShell, pytest/static checks, Arduino compile/upload/monitor, Flutter format/analyze/test/build/install, and diagnostic export. Use placeholders only for user-specific SSID/IP/token/COM port and explain how to discover each.

Create a test-record template with date/time, board revision, wiring revision, firmware/backend/app/model versions, power source, commands, actual result, measurements, artifact paths/hashes, and pass/fail. Include an evidence folder convention and redaction checklist.

Add troubleshooting decision trees for: boot/COM failure; strap-button issue; SD; Wi-Fi/hotspot IP; firewall/backend; auth; Whisper; Ollama model; vision hallucination/unreadable text; Piper/symbol pronunciation; low speaker volume/distortion; camera/profile; video corruption/dropped frames; BLE permissions; media transfer; ADC calibration; unknown charging state; sleep/wake; brownout/noise from LED/motor.

End with a complete demonstration sequence and shutdown/charging/storage procedure. Cross-link HOW_IT_WORKS, ARCHITECTURE, HARDWARE_WIRING, API references, TESTING, TROUBLESHOOTING, PROJECT_STATUS, requirement matrix, and evidence. Run all commands that can be executed locally, validate links, and explicitly label every unexecuted physical step. Do not state that hardware passed based only on compilation or mocked tests.
```

