# Local setup on Windows

## Backend

```powershell
cd 'E:\University Files\CS2\EE356\InspectPin'
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt -r backend\requirements-dev.txt
Copy-Item backend\.env.mock.example backend\.env
.\.venv\Scripts\python.exe backend\receiver.py
```

Mock mode validates transport only. For real models follow [INSTALLATION](INSTALLATION.md).

## Web

```powershell
cd web
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Simulator

```powershell
.\.venv\Scripts\python.exe simulator\inspectpin_simulator.py bootstrap
.\.venv\Scripts\python.exe simulator\inspectpin_simulator.py scenario backend\tests\fixtures\synthetic_nameplate_a.jpg
```

## Mobile

Install Flutter/Android Studio, then run `flutter pub get`, `flutter analyze`,
`flutter test` and `flutter run` in `mobile_app`. Flutter was unavailable during
the current acceptance run.

The backend bind error `WinError 10049` means `HOST` is not a local laptop
address. Use `127.0.0.1` for laptop-only testing or the current `ipconfig` Wi-Fi
IPv4 address for the device; update it whenever the hotspot changes.
