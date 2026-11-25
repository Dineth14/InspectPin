"""Approve a signed package on the laptop and wait for device confirmation."""
import argparse
import getpass
import json
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    token = ""

    def request(path, body=None):
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        if body is not None:
            headers["Content-Type"] = "application/json"
        payload = json.dumps(body).encode() if body is not None else None
        try:
            with urlopen(Request("http://127.0.0.1:5000/api/v1" + path, payload, headers), timeout=12) as response:
                return json.load(response)
        except HTTPError as exc:
            error = json.load(exc).get("error", {})
            raise SystemExit(error.get("message", f"Receiver returned {exc.code}")) from None

    token = request("/auth/login", {"email": input("InspectPin account email: "),
                                   "password": getpass.getpass("Password: ")})["access_token"]
    route = f"/devices/{args.device}/firmware"
    catalog = request(route)
    packages = [p for p in catalog["packages"] if p["version"] == args.version and p["compatible"]]
    if len(packages) != 1 or not catalog["online"]:
        raise SystemExit("Wake the device and check there is exactly one compatible package for this version.")
    package = packages[0]
    print(f"Target {args.device}, firmware {package['version']} ({package['build']}), {package['size']} bytes")
    print("Keep stable external power connected until the device restarts and reports completion.")
    if input("Type EXTERNAL POWER CONFIRMED to install: ").strip() != "EXTERNAL POWER CONFIRMED":
        raise SystemExit("Approval cancelled")
    ident = request(route, {"sha256": package["sha256"], "external_power_confirmed": True})["id"]
    started = time.monotonic()
    last = None
    while time.monotonic() - started < 365:
        catalog = request(route)
        update = catalog.get("update")
        if update and update["id"] == ident:
            snapshot = (update["state"], update["bytes"], update["detail"])
            if snapshot != last:
                print(f"{snapshot[0]} · {snapshot[1]} bytes · {snapshot[2]}", flush=True)
                last = snapshot
            if update["state"] == "confirmed":
                reported = catalog.get("installed") or {}
                if (reported.get("version"), reported.get("build")) == (package["version"], package["build"]):
                    print("Verified device version after restart.")
                    return
            if update["state"] in {"expired", "failed", "cancelled"}:
                raise SystemExit("Device has not confirmed installation.")
        time.sleep(2)
    raise SystemExit("No matching boot confirmation received. Consult the recovery guide.")


if __name__ == "__main__":
    main()
