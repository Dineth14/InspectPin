# Accessibility review

## Implemented

- Semantic HTML landmarks, headings, labels and native controls are used on web.
- Icon-only controls receive accessible names; decorative icon content is hidden from assistive technology.
- Flutter brand and device artwork expose semantic labels and exclude duplicate painted semantics.
- Keyboard focus uses a high-contrast cyan outline with offset.
- Status uses visible text in addition to colour.
- Dark and light palettes preserve strong text/surface contrast.
- Buttons meet a minimum 44 px web target and 48 logical pixel Flutter target.
- Responsive navigation remains reachable without horizontal page scrolling at supported breakpoints.
- Form failures use alert/status semantics and do not clear the form.
- Reduced-motion preferences suppress non-essential animation.
- Images use purpose-specific alternative text; conceptual product art is identified as conceptual.
- Missing or failed protected media has a visible fallback rather than an empty region.

## Manual checks still required

1. Run NVDA with Chrome on login, dashboard, history and inspection workspace.
2. Run VoiceOver/TalkBack on a built mobile application.
3. Confirm logical focus order at 320, 375, 768, 1024 and 1440 CSS pixels.
4. Test 200% browser zoom and the platform largest-text setting.
5. Verify contrast with an automated analyser after the browser runtime is repaired.
6. Test the inspection image zoom gesture alongside screen-reader navigation.

## Known limitations

The local in-app browser runtime could not start during this review because the user-level Codex model catalog was invalid. Therefore rendered keyboard, screen-reader and automated contrast checks are not claimed as complete. Source review and production compilation passed, but they do not replace those physical/manual checks.

