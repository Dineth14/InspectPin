# InspectPin mobile application

The Flutter application provides authenticated accounts, device telemetry,
remote PHOTO/flashlight/volume/haptic commands, inspection history, contextual
questions, and per-workspace AI provider/model configuration.

## Toolchain

Install the current stable Flutter SDK and Android Studio/SDK, then run:

```powershell
cd mobile_app
flutter create --platforms=android,ios .
flutter pub get
flutter analyze
flutter test
flutter build apk --release --dart-define=INSPECTPIN_API_URL=https://your-backend.example
```

The repository currently contains the reviewed Dart application sources but no
generated `android/` or `ios/` runner directories. `flutter create` generates
those platform files without replacing `lib/`, `test/`, assets or
`pubspec.yaml`. Review application IDs, signing, minimum OS versions, network
security configuration, icons and permissions before release.

## Connection policy

The login page accepts a private LAN HTTP backend for bench testing. Public or
remote hosts must use HTTPS. The selected origin and account token are stored in
platform secure storage. Signing out removes the account token; sign out before
switching servers.

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
