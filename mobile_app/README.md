# InspectPin mobile application

The Flutter application provides authenticated accounts, device telemetry,
remote PHOTO/volume/power-timeout commands, inspection history, contextual
questions, and per-workspace AI provider/model configuration. The current
product has no flashlight or vibration control, so neither appears in the UI
or remote command API.

## Toolchain

The Windows workstation now has a verified portable toolchain:

- Flutter 3.50.0 in `../.tools/flutter`
- Android SDK 36 and JDK 17 in `E:\InspectPinToolchain`
- application ID `ai.inspectpin.mobile`
- minimum Android SDK 24 and target SDK 36

Build and test from PowerShell with:

```powershell
cd mobile_app
..\.tools\flutter\bin\flutter.bat pub get
..\.tools\flutter\bin\flutter.bat analyze
..\.tools\flutter\bin\flutter.bat test
..\.tools\flutter\bin\flutter.bat build apk --debug --dart-define=INSPECTPIN_API_URL=http://172.20.10.4:5000
```

## Laptop browser build

Build and serve the laptop version with:

```powershell
cd mobile_app
..\.tools\flutter\bin\flutter.bat build web --release --dart-define=INSPECTPIN_API_URL=http://127.0.0.1:5000
cd ..
.\.venv\Scripts\python.exe -m http.server 5180 --bind 127.0.0.1 --directory mobile_app\build\web
```

Set `CORS_ORIGIN=http://127.0.0.1:5180` in `backend/.env`, restart the backend,
then open `http://127.0.0.1:5180`. CORS uses an explicit allow-list; do not use
a wildcard origin with authenticated product APIs.

The Android runner is checked into the repository. The generated test package
is `build/app/outputs/flutter-apk/app-debug.apk`. It uses Android's debug key
and is suitable only for bench testing. A commercial release requires a
company-controlled upload key/keystore and Play App Signing configuration.

An iOS binary cannot be compiled or signed on Windows. Generate the iOS runner
and perform Xcode signing, physical-device testing and App Store archiving on a
Mac before claiming iPhone support. The shared Flutter application code is
platform independent.

## Connection policy

The login page accepts a private LAN HTTP backend for bench testing. The Android
manifest permits cleartext transport for that controlled development case, and
the Dart client rejects public cleartext origins. Public or remote hosts must
use HTTPS. Before store release, replace the broad Android cleartext permission
with build-flavor-specific network security configuration. The selected origin
and account token are stored in platform secure storage. Signing out removes
the account token; sign out before switching servers.

## AI configuration

Settings -> Configure AI selects Ollama, OpenAI API, Anthropic Claude API or
DeepSeek for text and a supported vision provider/model. Cloud keys are sent
only to the backend, encrypted there, and never returned to the app. Use the
explicit provider test after saving. Model IDs are deliberately entered rather
than hard-coded because provider availability and retirement schedules change.

## Hardware acceptance

Before release, test physical Android and iOS devices across foreground,
background, network handoff, expired session, offline device, deep sleep/wake,
permission denial and slow/failed provider conditions. App UI success does not
substitute for electrical, battery or actuator safety validation.
