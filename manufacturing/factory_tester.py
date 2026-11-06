"""InspectPin Rev N USB factory-test runner.

The target firmware is the authority for measurements. This program records its
JSON records without turning BLOCKED/SKIPPED work into a pass.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

VALID_STATUSES = {"PASS", "FAIL", "SKIPPED", "BLOCKED"}
SAFE_BOARD_ID = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")


@dataclass(frozen=True)
class TestRecord:
    test: str
    status: str
    detail: str = ""
    measurement: str = ""
    tolerance: str = ""


def parse_fct_line(line: str) -> TestRecord | None:
    """Parse one target JSON line; ignore banners and CSV duplicates."""
    line = line.strip()
    if not line.startswith("{"):
        return None
    try:
        item = json.loads(line)
    except json.JSONDecodeError:
        return None
    if item.get("type") != "fct":
        return None
    test = str(item.get("test", "")).strip()
    status = str(item.get("status", "")).upper().strip()
    if not test or status not in VALID_STATUSES:
        return None
    return TestRecord(
        test=test,
        status=status,
        detail=str(item.get("detail", "")),
        measurement=str(item.get("measurement", "")),
        tolerance=str(item.get("tolerance", "")),
    )


def overall_status(records: Iterable[TestRecord]) -> str:
    values = list(records)
    if not values or any(record.status == "FAIL" for record in values):
        return "FAIL"
    if any(record.status == "BLOCKED" for record in values):
        return "BLOCKED"
    if all(record.status == "SKIPPED" for record in values):
        return "SKIPPED"
    return "PASS"


def write_report(output: Path, board_id: str, port: str, records: list[TestRecord], raw: list[str]) -> tuple[Path, Path]:
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stem = f"{board_id}_{stamp}"
    json_path, csv_path = output / f"{stem}.json", output / f"{stem}.csv"
    payload = {
        "schema": "inspectpin-revn-fct/v1",
        "board_id": board_id,
        "port": port,
        "captured_at_utc": stamp,
        "overall": overall_status(records),
        "counts": {status: sum(r.status == status for r in records) for status in sorted(VALID_STATUSES)},
        "results": [asdict(record) for record in records],
        "raw_serial": raw,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["board_id", "captured_at_utc", "test", "status", "detail", "measurement", "tolerance"])
        writer.writeheader()
        for record in records:
            writer.writerow({"board_id": board_id, "captured_at_utc": stamp, **asdict(record)})
    return json_path, csv_path


def collect(port: str, commands: list[str], timeout: float, quiet: float) -> tuple[list[TestRecord], list[str]]:
    try:
        import serial  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Install manufacturing/requirements.txt before using a serial port") from exc
    records: list[TestRecord] = []
    raw: list[str] = []
    with serial.Serial(port, 115200, timeout=0.25, write_timeout=2) as device:
        time.sleep(1.5)
        device.reset_input_buffer()
        for command in commands:
            device.write((command + "\n").encode("ascii"))
            device.flush()
            deadline, last_result = time.monotonic() + timeout, None
            while time.monotonic() < deadline:
                data = device.readline()
                if data:
                    line = data.decode("utf-8", errors="replace").rstrip()
                    raw.append(line)
                    print(line)
                    parsed = parse_fct_line(line)
                    if parsed:
                        records.append(parsed)
                        last_result = time.monotonic()
                elif last_result is not None and time.monotonic() - last_result >= quiet:
                    break
    return records, raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run and archive InspectPin Rev N factory tests")
    parser.add_argument("--port", required=True, help="Native USB CDC port, for example COM7")
    parser.add_argument("--board-id", required=True, help="Unique serial/lot identifier")
    parser.add_argument("--output", type=Path, default=Path("manufacturing/reports"))
    parser.add_argument("--commands", nargs="+", default=["all"], help="Target commands in execution order")
    parser.add_argument("--timeout", type=float, default=120.0, help="Maximum seconds per command")
    parser.add_argument("--quiet", type=float, default=4.0, help="Finish after this quiet period following a result")
    args = parser.parse_args(argv)
    if not SAFE_BOARD_ID.fullmatch(args.board_id):
        parser.error("--board-id must use 1-64 letters, digits, dot, underscore or hyphen")
    if "wdt_arm" in args.commands:
        parser.error("wdt_arm is destructive and must be run manually per the operator procedure")
    try:
        records, raw = collect(args.port, args.commands, args.timeout, args.quiet)
        json_path, csv_path = write_report(args.output, args.board_id, args.port, records, raw)
    except (OSError, RuntimeError) as exc:
        print(f"factory tester error: {exc}", file=sys.stderr)
        return 2
    overall = overall_status(records)
    print(f"overall={overall} json={json_path} csv={csv_path}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
