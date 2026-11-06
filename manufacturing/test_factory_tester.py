import json

from factory_tester import TestRecord as Record, overall_status, parse_fct_line, write_report


def test_parser_accepts_only_valid_fct_json():
    record = parse_fct_line('{"type":"fct","test":"i2c","status":"PASS","measurement":"0x20;0x40"}')
    assert record == Record("i2c", "PASS", measurement="0x20;0x40")
    assert parse_fct_line("FCTCSV,i2c,PASS") is None
    assert parse_fct_line('{"type":"fct","test":"x","status":"MADE_UP"}') is None


def test_overall_never_converts_blocked_or_fail_to_pass():
    assert overall_status([Record("a", "PASS"), Record("b", "BLOCKED")]) == "BLOCKED"
    assert overall_status([Record("a", "FAIL"), Record("b", "BLOCKED")]) == "FAIL"
    assert overall_status([]) == "FAIL"


def test_reports_preserve_status(tmp_path):
    records = [Record("camera", "BLOCKED", "needs hardware")]
    json_path, csv_path = write_report(tmp_path, "REVN-001", "COM9", records, ["raw"])
    assert json.loads(json_path.read_text())["overall"] == "BLOCKED"
    assert "BLOCKED" in csv_path.read_text()
