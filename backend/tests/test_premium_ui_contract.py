from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_brand_assets_and_reference_disclosure_exist():
    required = (
        "assets/branding/inspectpin-wordmark-dark.svg",
        "assets/branding/inspectpin-wordmark-light.svg",
        "assets/branding/inspectpin-compact.svg",
        "assets/branding/inspectpin-icon.svg",
        "assets/branding/inspectpin-device-concept.svg",
    )
    assert all((ROOT / item).is_file() for item in required)
    disclosure = source("assets/branding/REFERENCE_STATUS.md").lower().replace("\n", " ")
    assert "not present" in disclosure


def test_web_uses_secure_session_and_truthful_simulator_labels():
    app = source("web/src/App.tsx")
    assert "sessionStorage" in app
    assert "localStorage.setItem('inspectpin_token'" not in app
    assert "SIMULATED" in app
    assert "CONCEPT VISUAL" in app
    assert "Unavailable" in source("web/src/api.ts")


def test_web_and_mobile_share_navigation_and_accessibility_foundations():
    web = source("web/src/App.tsx")
    mobile = source("mobile_app/lib/features/shell/home_shell.dart")
    for destination in ("Home", "Inspections", "Assistant", "Device", "Settings"):
        assert destination in web
        assert destination in mobile
    css = source("web/src/styles.css")
    assert "prefers-reduced-motion" in css
    assert "focus-visible" in css
    assert "@media(max-width:560px)" in css


def test_mobile_has_no_invalid_custom_font_weight_and_uses_secure_storage():
    dart = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "mobile_app/lib").rglob("*.dart"))
    assert "FontWeight.w750" not in dart
    assert "FlutterSecureStorage" in dart
    assert "InspectPinWordmark" in dart
    assert "DeviceConcept" in dart

