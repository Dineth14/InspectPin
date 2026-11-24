"""Own the foreground Windows demo session and stop only its new children."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import webbrowser
from urllib.request import urlopen

from open_laptop_app import is_inspectpin

ROOT = Path(__file__).resolve().parents[1]
EVENT = "Local\\InspectPinEvaluationSession"


def get(url):
    with urlopen(url, timeout=2) as response:
        return json.load(response)


def available(check):
    try:
        return check()
    except (OSError, ValueError):
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stop", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    from ctypes import wintypes as w
    kernel.CreateEventW.argtypes = [w.LPVOID, w.BOOL, w.BOOL, w.LPCWSTR]
    kernel.CreateEventW.restype = w.HANDLE
    kernel.SetEvent.argtypes = kernel.CloseHandle.argtypes = [w.HANDLE]
    kernel.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
    event = kernel.CreateEventW(None, True, False, EVENT)
    if not event:
        raise ctypes.WinError(ctypes.get_last_error())
    existing = ctypes.get_last_error() == 183
    children = []
    logs = ROOT / ".build"
    logs.mkdir(exist_ok=True)

    def ensure(name, check, command, env=None):
        if available(check):
            print("Reusing", name, flush=True)
            return
        with (logs / ("demo-" + name + ".log")).open("ab") as log:
            child = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=log,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
        children.append(child)
        for _ in range(120):
            if available(check):
                return
            if child.poll() is not None or kernel.WaitForSingleObject(event, 500) == 0:
                break
        raise SystemExit(f"{name} startup interrupted or failed. See {logs}/demo-{name}.log")

    try:
        if args.stop:
            if existing:
                kernel.SetEvent(event)
            print("Stop requested." if existing else "No launcher session.")
            return
        ui = "http://127.0.0.1:5180"
        if existing:
            print("InspectPin launcher already running.")
            if not args.no_browser and is_inspectpin(ui):
                webbrowser.open(ui)
            return
        kernel.SetThreadExecutionState(0x80000001)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("1.1.1.1", 53))
            ip = probe.getsockname()[0]
        tags = "http://127.0.0.1:11434/api/tags"
        ensure("ollama", lambda: "models" in get(tags), [shutil.which("ollama") or "ollama", "serve"])
        missing = {"qwen2.5vl:3b", "llama3.2:3b"} - {m["name"] for m in get(tags)["models"]}
        if missing:
            raise SystemExit("Missing local models: " + ", ".join(sorted(missing)))
        origin = f"http://{ip}:5000"
        def ready():
            return (get(origin + "/healthz").get("service") == "InspectPin AI" and
                    get(origin + "/api/v1/ready").get("database") == "ok")
        ensure("receiver", ready, [sys.executable, "backend/receiver.py"],
               dict(os.environ, HOST="0.0.0.0", PORT="5000", WHISPER_LOCAL_ONLY="true",
                    LLM_PROVIDER="ollama", VISION_PROVIDER="ollama", STT_PROVIDER="whisper",
                    TTS_PROVIDER="piper", LLM_MODEL="llama3.2:3b", VISION_MODEL="qwen2.5vl:3b"))
        ensure("app", lambda: is_inspectpin(ui), [sys.executable, "scripts/open_laptop_app.py", "--serve"])
        print(f"Receiver for board and phone: {origin}\nLaptop application: {ui}\nKeep this window open.", flush=True)
        if not args.no_browser:
            webbrowser.open(ui)
        while kernel.WaitForSingleObject(event, 1000) == 258:
            if any(child.poll() is not None for child in children):
                raise SystemExit("A demo process exited. Check .build/demo-*.log.")
    finally:
        for child in reversed(children):
            if child.poll() is None:
                subprocess.run(["taskkill", "/PID", str(child.pid), "/T", "/F"], capture_output=True)
        kernel.CloseHandle(event)


if __name__ == "__main__":
    main()
