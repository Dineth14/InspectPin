"""Provision private offline/receiver signing keys or publish a signed app binary."""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from inspectpin.firmware_package import (  # noqa: E402
    HARDWARE, SLOT_BYTES, TARGET, canonical_manifest, release_number, sign, validate_package,
)


def create_key(path):
    key = ec.generate_private_key(ec.SECP256R1())
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as out:
        out.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                    serialization.NoEncryption()))
    return key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    init = sub.add_parser("init")
    init.add_argument("--offline-key-dir", type=Path, required=True)
    init.add_argument("--receiver-dir", type=Path, required=True)
    build = sub.add_parser("build-identity")
    build.add_argument("--version", required=True)
    build.add_argument("--build", required=True)
    publish = sub.add_parser("publish")
    publish.add_argument("--receiver-dir", type=Path, required=True)
    publish.add_argument("--key", type=Path, required=True)
    publish.add_argument("--binary", type=Path, required=True)
    publish.add_argument("--version", required=True)
    publish.add_argument("--build", required=True)
    publish.add_argument("--notes", required=True)
    args = parser.parse_args()
    firmware = ROOT / "firmware/InspectPinAI"
    if args.action == "init":
        offline = args.offline_key_dir.resolve()
        receiver = args.receiver_dir.resolve()
        if offline == receiver or any(p.is_relative_to(ROOT) for p in (offline, receiver)):
            parser.error("Use separate private directories outside the repository")
        offline.mkdir(parents=True, exist_ok=True, mode=0o700)
        receiver.mkdir(parents=True, exist_ok=True, mode=0o700)
        release = create_key(offline / "release-private.pem")
        grant = create_key(receiver / "grant-private.pem")
        (receiver / "release-public.pem").write_bytes(release)
        (firmware / "ota_trust.local.h").write_text(
            '#pragma once\n'
            f'constexpr char otaReleasePublicKey[]=R"pem({release.decode("ascii")})pem";\n'
            f'constexpr char otaGrantPublicKey[]=R"pem({grant.decode("ascii")})pem";\n',
            encoding="ascii")
        return
    if args.action == "build-identity":
        import re

        if not re.fullmatch(r"[a-zA-Z0-9_.-]{1,48}", args.build):
            parser.error("Invalid build identifier")
        (firmware / "firmware_build.local.h").write_text(
            f'#pragma once\n#define IP_FIRMWARE_VERSION "{args.version}"\n'
            f'#define IP_FIRMWARE_RELEASE {release_number(args.version)}UL\n'
            f'#define IP_FIRMWARE_BUILD_ID "{args.build}"\n', encoding="ascii")
        return
    if args.binary.stat().st_size > SLOT_BYTES:
        parser.error("Image exceeds the 0x330000-byte application slot")
    image = args.binary.read_bytes()
    if args.version.encode() not in image or args.build.encode() not in image:
        parser.error("Image does not contain the requested version and build")
    if not 1 <= len(args.notes) <= 1000:
        parser.error("Release notes must be 1–1000 characters")
    ident = hashlib.sha256(image).hexdigest()
    manifest = {"version": args.version, "build": args.build, "target": TARGET,
                "hardware": HARDWARE, "size": len(image), "sha256": ident, "slot_bytes": SLOT_BYTES,
                "notes": args.notes}
    manifest["signature"] = sign(args.key, canonical_manifest(manifest))
    validate_package(manifest, image, args.receiver_dir / "release-public.pem")
    artifacts = args.receiver_dir / "packages"
    artifacts.mkdir(mode=0o700, exist_ok=True)
    (artifacts / f"{ident}.bin").write_bytes(image)
    pending = artifacts / f"{ident}.tmp"
    pending.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    pending.replace(artifacts / f"{ident}.json")
    print(f"Published {args.version} {args.build}, {len(image)} bytes, SHA-256 {ident}")


if __name__ == "__main__":
    main()
