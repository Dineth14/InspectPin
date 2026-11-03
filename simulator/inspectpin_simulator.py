"""Windows-friendly InspectPin virtual device using the production HTTP contract.

Simulator data is always marked as simulated.  It does not claim to perform
camera, microphone, battery or hardware validation.
"""
from __future__ import annotations

import argparse
import json
import math
import struct
import sys
import time
import wave
from dataclasses import asdict, dataclass
from io import BytesIO
from pathlib import Path

import requests


@dataclass
class SimulatorState:
    api_url: str
    access_token: str
    device_id: str
    device_token: str
    battery_percent: float = 83.0
    battery_voltage: float = 4.02
    storage_free: int = 7_500_000_000
    storage_total: int = 8_000_000_000
    sd_present: bool = True
    online: bool = True
    active_inspection: str = ""


class VirtualInspectPin:
    def __init__(self, state: SimulatorState, timeout: float = 10.0):
        self.state, self.timeout = state, timeout

    @property
    def user_headers(self):
        return {"Authorization": "Bearer " + self.state.access_token}

    @property
    def device_headers(self):
        return {"X-Device-ID": self.state.device_id, "X-Device-Token": self.state.device_token}

    def request(self, method: str, path: str, **kwargs):
        if not self.state.online:
            raise RuntimeError("SIMULATED_OFFLINE: reconnect before network operations")
        response = requests.request(method, self.state.api_url.rstrip("/") + path,
                                    timeout=self.timeout, allow_redirects=False, **kwargs)
        if response.status_code >= 400:
            try:
                detail = response.json().get("error", response.json())
            except ValueError:
                detail = response.text[:200]
            raise RuntimeError(f"HTTP_{response.status_code}: {detail}")
        return response

    def heartbeat(self):
        return self.request("POST", "/api/v1/device/heartbeat", headers=self.device_headers, json={
            "battery_percent": self.state.battery_percent,
            "battery_voltage": self.state.battery_voltage,
            "battery_estimated": True,
            "charge_state": "battery",
            "storage_free": self.state.storage_free,
            "storage_total": self.state.storage_total,
            "sd_present": self.state.sd_present,
            "wifi_rssi": -42,
            "connection": "simulator",
        }).json()

    def poll_commands(self):
        commands = self.request("GET", "/api/v1/device/commands", headers=self.device_headers).json()["items"]
        for command in commands:
            result = {"simulated": True, "message": f"Simulated {command['command_type']} completed"}
            self.request("POST", f"/api/v1/device/commands/{command['id']}/ack",
                         headers=self.device_headers, json={"status": "completed", "result": result})
        return commands

    def photo(self, image: Path):
        if not self.state.sd_present:
            raise RuntimeError("SIMULATED_SD_ABSENT: photo retained nowhere; operation rejected")
        pixels = image.read_bytes()
        created = self.request("POST", "/api/v1/inspections", headers=self.user_headers, json={
            "device_id": self.state.device_id,
            "title": "Simulator photo inspection",
            "simulated": True,
        }).json()
        self.request("POST", f"/api/v1/inspections/{created['id']}/media",
                     headers={**self.user_headers, "Content-Type": "image/jpeg"}, data=pixels)
        job = self.request("POST", f"/api/v1/inspections/{created['id']}/analyze",
                           headers={**self.user_headers, "Idempotency-Key": "sim-photo-" + created["id"]},
                           json={"question": "Identify only visible details and state uncertainty."}).json()
        self.state.active_inspection = created["id"]
        return created, job

    def wait_product_job(self, job_id: str, deadline: float = 30.0):
        end = time.monotonic() + deadline
        while time.monotonic() < end:
            result = self.request("GET", f"/api/v1/processing-jobs/{job_id}", headers=self.user_headers).json()
            if result["status"] in {"completed", "failed"}:
                return result
            time.sleep(0.1)
        raise RuntimeError("SIMULATED_TIMEOUT: product job did not finish")

    def ask_inspection(self, inspection_id: str, question: str):
        job = self.request("POST", f"/api/v1/inspections/{inspection_id}/questions",
                           headers={**self.user_headers, "Idempotency-Key": "sim-question-" + inspection_id},
                           json={"question": question}).json()
        return self.wait_product_job(job["id"])

    @staticmethod
    def mock_wav(seconds: float = 1.0) -> bytes:
        buffer = BytesIO()
        rate = 16000
        with wave.open(buffer, "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(rate)
            samples = bytearray()
            for index in range(int(rate * seconds)):
                sample = int(2500 * math.sin(2 * math.pi * 220 * index / rate))
                samples.extend(struct.pack("<h", sample))
            output.writeframes(bytes(samples))
        return buffer.getvalue()

    def ask(self):
        headers = {**self.device_headers, "Content-Type": "audio/wav"}
        return self.request("POST", "/api/v1/jobs/voice", headers=headers, data=self.mock_wav()).json()

    def wait_ai_job(self, job_id: str, deadline: float = 30.0):
        end = time.monotonic() + deadline
        while time.monotonic() < end:
            result = self.request("GET", f"/api/v1/jobs/{job_id}", headers=self.device_headers).json()
            if result["status"] in {"completed", "failed"}:
                return result
            time.sleep(0.1)
        raise RuntimeError("SIMULATED_TIMEOUT: AI job did not finish")


def bootstrap(url: str, email: str, password: str, name: str, device_id: str) -> SimulatorState:
    session = requests.Session()
    endpoint = url.rstrip("/")
    login = session.post(endpoint + "/api/v1/auth/login", json={"email": email, "password": password}, timeout=10)
    if login.status_code == 401:
        login = session.post(endpoint + "/api/v1/auth/register",
                             json={"name": name, "email": email, "password": password}, timeout=10)
    login.raise_for_status()
    access = login.json()["access_token"]
    pair = session.post(endpoint + "/api/v1/devices/pair",
                        headers={"Authorization": "Bearer " + access}, json={
                            "device_id": device_id, "name": "InspectPin Simulator",
                            "model": "virtual-inspectpin", "hardware_revision": "sim-1",
                            "firmware_version": "sim-1.0",
                        }, timeout=10)
    pair.raise_for_status()
    return SimulatorState(endpoint, access, device_id, pair.json()["device_token"])


def load_state(path: Path) -> SimulatorState:
    return SimulatorState(**json.loads(path.read_text(encoding="utf-8")))


def save_state(path: Path, state: SimulatorState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(state), indent=2), encoding="utf-8")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="InspectPin virtual device (all events are simulated)")
    result.add_argument("--state", type=Path, default=Path(".build/simulator-state.json"))
    commands = result.add_subparsers(dest="command", required=True)
    setup = commands.add_parser("bootstrap")
    setup.add_argument("--url", default="http://127.0.0.1:5000")
    setup.add_argument("--email", default="simulator@inspectpin.local")
    setup.add_argument("--password", default="local-simulator-password")
    setup.add_argument("--name", default="Simulator Owner")
    setup.add_argument("--device-id", default="inspectpin-simulator-01")
    commands.add_parser("heartbeat")
    photo = commands.add_parser("photo")
    photo.add_argument("image", type=Path)
    commands.add_parser("ask")
    commands.add_parser("commands")
    online = commands.add_parser("online")
    online.add_argument("value", choices=("on", "off"))
    sd = commands.add_parser("sd")
    sd.add_argument("value", choices=("inserted", "removed"))
    battery = commands.add_parser("battery")
    battery.add_argument("percent", type=float)
    scenario = commands.add_parser("scenario")
    scenario.add_argument("image", type=Path)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "bootstrap":
            state = bootstrap(args.url, args.email, args.password, args.name, args.device_id)
            save_state(args.state, state)
            print(json.dumps({"event": "SIMULATOR_BOOTSTRAPPED", "device_id": state.device_id}, indent=2))
            return 0
        state = load_state(args.state)
        device = VirtualInspectPin(state)
        if args.command == "heartbeat":
            result = device.heartbeat()
        elif args.command == "commands":
            result = device.poll_commands()
        elif args.command == "photo":
            inspection, job = device.photo(args.image)
            result = {"inspection": inspection, "job": device.wait_product_job(job["id"])}
        elif args.command == "ask":
            job = device.ask()
            result = device.wait_ai_job(job["id"])
        elif args.command == "online":
            state.online = args.value == "on"
            result = {"simulated_online": state.online}
        elif args.command == "sd":
            state.sd_present = args.value == "inserted"
            result = {"simulated_sd_present": state.sd_present}
        elif args.command == "battery":
            state.battery_percent = max(0.0, min(100.0, args.percent))
            result = device.heartbeat()
        else:
            heartbeat = device.heartbeat()
            inspection, photo_job = device.photo(args.image)
            photo_result = device.wait_product_job(photo_job["id"])
            assistant_result = device.ask_inspection(inspection["id"], "Explain one visible detail and state uncertainty.")
            voice_job = device.ask()
            voice_result = device.wait_ai_job(voice_job["id"])
            result = {"heartbeat": heartbeat, "inspection_id": inspection["id"],
                      "photo_job": photo_result, "assistant_job": assistant_result, "voice_job": voice_result,
                      "notice": "All results in this scenario are simulator/mock results."}
        save_state(args.state, state)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, requests.RequestException) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
