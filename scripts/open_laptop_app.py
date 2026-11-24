"""Open the compiled laptop app without starting a compiler or an AI worker."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen
import webbrowser

WEB_ROOT = Path(__file__).resolve().parents[1] / "mobile_app/build/web"


def is_inspectpin(origin):
    try:
        with urlopen(origin + "/manifest.json", timeout=2) as response:
            return json.loads(response.read(8192)).get("name") == "InspectPin AI"
    except (URLError, OSError, ValueError, AttributeError):
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-browser", action="store_true", help="Check the app server without opening a tab")
    parser.add_argument("--port", type=int, default=5180)
    parser.add_argument("--serve", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    origin = f"http://127.0.0.1:{args.port}"
    if args.serve:
        handler = partial(SimpleHTTPRequestHandler, directory=str(WEB_ROOT))
        with ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
            server.serve_forever()
        return
    if not is_inspectpin(origin):
        if not (WEB_ROOT / "main.dart.js").is_file():
            raise SystemExit("Compiled laptop app missing. See docs/RELEASE_NOTES.md for the web build command.")
        options = ({"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt"
                   else {"start_new_session": True})
        child = subprocess.Popen([sys.executable, __file__, "--serve", "--port", str(args.port)],
                                 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, **options)
        for _ in range(30):
            if is_inspectpin(origin):
                break
            if child.poll() is not None:
                raise SystemExit(f"Could not serve InspectPin on port {args.port}. Check which process owns the port.")
            time.sleep(0.1)
        else:
            child.terminate()
            raise SystemExit(f"InspectPin did not start at {origin}.")
    print(f"InspectPin app: {origin}")
    if not args.no_browser:
        webbrowser.open_new_tab(origin)


if __name__ == "__main__":
    main()
