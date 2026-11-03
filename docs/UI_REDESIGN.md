# Premium application redesign

## Outcome

The existing React/Vite web application and Flutter mobile application now share one InspectPin visual language without replacing the working API, authentication, device, inspection or media contracts.

## Before and after

| Area | Previous implementation | Redesigned implementation |
|---|---|---|
| Identity | Text-only product name | Reusable SVG/PNG wordmark, compact mark and app icon |
| Navigation | Utility tabs/basic shell | Consistent five-destination rail or bottom navigation |
| Home | Flat telemetry blocks | Device-led instrument hero with real battery, storage and Wi-Fi |
| Inspections | Basic list/detail | Searchable evidence library and three-part inspection workspace |
| Assistant | Generic question control | Context-bound evidence conversation with processing feedback |
| Device | Basic paired record | Connection, hardware and truthful pairing controls |
| Themes | Limited platform styling | Matched Midnight and Precision Light systems |
| Resilience | Ad-hoc loading/error text | Skeletons, intentional empty states, error boundary and retry messaging |
| Privacy | Token persisted in browser storage | Session token in `sessionStorage`; legacy token migrated and removed |

## Web implementation

`web/src/App.tsx` owns the product views while `web/src/components/` contains reusable brand, icon, media, status, loading and error-boundary primitives. `web/src/tokens.css` defines foundations, and `web/src/styles.css` implements the responsive layouts.

Authenticated evidence images are downloaded through the existing ownership-checked API and displayed using object URLs that are revoked on cleanup. No provider secret is shipped to the browser. Device and inspection values are read from the API; no display telemetry is invented.

## Mobile implementation

The Flutter app adds an initial splash, secure onboarding, premium authentication and a five-destination home shell. `mobile_app/lib/design/` contains cross-screen theme and brand primitives. Tokens remain in encrypted platform storage through the existing secure storage abstraction.

The mobile detail screen can fetch protected evidence bytes, zoom the original image, show structured findings and continue the inspection conversation. Battery percentage remains explicitly identified as an estimate when derived from voltage.

## Reference limitation

Only the text prompt was attached. The referenced “Internal Arrangement Concept” image was not available in the attachment directory or repository. The delivered concept illustration is therefore an original, code-native reconstruction and is labelled accordingly in the product and asset documentation.

## Files of interest

- Brand source and exports: `assets/branding/`
- Web design: `web/src/tokens.css`, `web/src/styles.css`, `web/src/components/`
- Mobile design: `mobile_app/lib/design/`
- Onboarding: `mobile_app/lib/features/onboarding/onboarding_screen.dart`
- Export utility: `scripts/export_brand_pngs.py`

## Launch the redesigned applications

Start the backend from the repository root, then start the web client:

```powershell
.\.venv\Scripts\python.exe backend\receiver.py
Set-Location web
npm.cmd run dev
```

Open `http://127.0.0.1:5173`. For mock-only design data, use the simulator commands in the repository README; all generated records remain visibly labelled as simulated.

For Flutter, install a compatible Flutter SDK and run from `mobile_app`:

```powershell
flutter pub get
flutter run --dart-define=INSPECTPIN_API_URL=http://10.0.2.2:5000
```

Replace `10.0.2.2` with the laptop LAN address for a physical phone. Development HTTP must be replaced by HTTPS for production.

## Verification completed

- Python: 150 tests passed.
- Web: 3 Vitest tests passed.
- Web production build: TypeScript and Vite passed.
- Quality: Ruff, Python compilation, dependency validation and Markdown-link validation passed.
- Mobile: source contracts and delimiter checks passed; native Flutter compilation is pending because Flutter/Dart are not installed on this workstation.

