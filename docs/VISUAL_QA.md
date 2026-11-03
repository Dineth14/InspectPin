# Visual QA record

Date: 2026-11-03

## Prepared QA environment

- Backend: local Flask/Waitress instance with all AI providers set to `mock`.
- Web: Vite development server.
- Account: local design-QA account.
- Device: `inspectpin-design-qa`, explicitly marked simulator.
- Evidence: repository synthetic nameplate fixture.
- Scenario: heartbeat, photo analysis, inspection follow-up and voice transport all completed through production HTTP contracts.

## Automated evidence

- SVG sources were exported to transparent PNGs at 192, 512, 540, 1024 and 1080 px variants.
- The 1080 px dark wordmark export was inspected for transparency, spacing, cyan accent and legibility.
- TypeScript compilation and the Vite production build passed.
- Responsive CSS includes explicit desktop, tablet and narrow-phone layouts at 1240, 860 and 560 px boundaries.
- Static contracts verify the brand files, concept labelling, privacy-sensitive token storage, responsive navigation and matched mobile/web destinations.
- The complete automated run passed 150 Python tests and 3 web tests; the production web bundle compiled successfully.

## Rendered browser QA status

The required in-app browser was invoked twice but exited before a tab could open. Its diagnostic was:

```text
failed to parse model_catalog_json path ...ollama-launch-models.json as JSON:
missing field base_instructions at line 528 column 5
```

This file is outside the project and was not modified. Consequently, desktop/mobile screenshots are not fabricated and rendered viewport QA remains outstanding. After that user-level configuration is repaired, repeat the matrix below and save screenshots under `docs/evidence/ui/`.

## Viewport matrix to complete

| View | 1440×1000 | 1024×768 | 390×844 | Checks |
|---|---|---|---|---|
| Login | Pending | Pending | Pending | Wordmark, form, concept label, no overflow |
| Home | Pending | Pending | Pending | Real telemetry, simulator labels, nav switch |
| Inspections | Pending | Pending | Pending | Search/filter, card rhythm, empty state |
| Workspace | Pending | Pending | Pending | Image, findings and conversation order |
| Device | Pending | Pending | Pending | Pairing copy, offline/online state |
| Settings | Pending | Pending | Pending | Theme switch and contrast |

## Acceptance rule

Do not mark visual QA complete until screenshots exist for all three widths, keyboard traversal is recorded, browser console errors are zero, protected images load, and both themes have been checked.

