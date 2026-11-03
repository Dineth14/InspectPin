from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MOBILE = ROOT / "mobile_app"


def test_mobile_battery_model_preserves_estimate_and_charge_validity():
    model = (MOBILE / "lib/features/dashboard/battery_status.dart").read_text(encoding="utf-8")
    card = (MOBILE / "lib/features/dashboard/battery_card.dart").read_text(encoding="utf-8")
    assert "voltage_v" in model
    assert "estimated_percent" in model
    assert "uncertainty_v" in model
    assert "critical" in model and "BatteryWarning.critical" in model
    assert "charge_valid" in model
    assert "not inferred from voltage" in card


def test_mobile_sources_include_battery_unit_and_widget_tests():
    assert (MOBILE / "test/battery_status_test.dart").exists()
    assert (MOBILE / "test/battery_card_test.dart").exists()
    assert (MOBILE / "pubspec.yaml").exists()
