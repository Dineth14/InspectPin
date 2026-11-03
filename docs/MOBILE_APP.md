# Flutter mobile app

The existing Flutter project was retained and redesigned as a premium InspectPin
instrument interface. It supports Android-first/iOS-capable architecture,
explicit Midnight/Precision Light themes, branded onboarding, login/registration,
encrypted platform token storage, session restore/expiry, paired device telemetry,
battery voltage and estimated percentage, charge validity, searchable inspection
history/detail, authenticated image zoom, contextual questions, simulator labels,
PHOTO commands, pairing and sign-out.

Configure the backend at build time:

```powershell
flutter run --dart-define=INSPECTPIN_API_URL=http://10.0.2.2:5000
```

Android emulator uses `10.0.2.2`; a phone uses the laptop LAN IP and must be on
the same trusted network. HTTP is development-only. Production requires HTTPS.
Phone microphone recording, phone photo upload, push notifications, report
sharing and self-service account deletion remain listed limitations, not hidden
mock controls.
