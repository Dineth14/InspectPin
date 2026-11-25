"""Signed InspectPin firmware manifest shared by the receiver and packaging CLI."""
import base64
import binascii
import hashlib
import re

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

TARGET = "esp32s3"
HARDWARE = "xiao-esp32s3-sense-single-layer"
SLOT_BYTES = 0x330000
MANIFEST_FIELDS = ("version", "build", "target", "hardware", "size", "sha256", "slot_bytes")


def maintenance_proof(folder):
    return hashlib.sha256(b"InspectPin local maintenance v1\0" + (folder / "grant-private.pem").read_bytes()).hexdigest()


def release_number(version):
    if not isinstance(version, str) or not re.fullmatch(r"(?:0|[1-9]\d{0,2})(?:\.(?:0|[1-9]\d{0,2})){2}", version, re.ASCII):
        raise ValueError("Expected a numeric semantic firmware version")
    major, minor, patch = map(int, version.split("."))
    return major * 1_000_000 + minor * 1000 + patch


def canonical_manifest(manifest):
    release_number(manifest.get("version"))
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,48}", manifest.get("build", "")):
        raise ValueError("Invalid build identifier")
    if manifest.get("target") != TARGET or manifest.get("hardware") != HARDWARE:
        raise ValueError("Unsupported firmware target")
    if type(manifest.get("size")) is not int or not 256 <= manifest["size"] <= SLOT_BYTES:
        raise ValueError("Invalid firmware size")
    if manifest.get("slot_bytes") != SLOT_BYTES or not re.fullmatch(r"[a-f0-9]{64}", manifest.get("sha256", "")):
        raise ValueError("Invalid slot requirement or digest")
    return ("InspectPin firmware v1\n" + "".join(f"{manifest[key]}\n" for key in MANIFEST_FIELDS)).encode("ascii")


def canonical_grant(device, update, challenge, digest):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", device):
        raise ValueError("Invalid device identity")
    for value, length in ((update, 32), (challenge, 32), (digest, 64)):
        if not re.fullmatch(rf"[a-f0-9]{{{length}}}", value):
            raise ValueError("Invalid OTA authorization metadata")
    return f"InspectPin approval v1\n{device}\n{update}\n{challenge}\n{digest}\n".encode("ascii")


def sign(key_path, payload):
    key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
    if not isinstance(key, ec.EllipticCurvePrivateKey) or not isinstance(key.curve, ec.SECP256R1):
        raise ValueError("Expected an ECDSA P-256 signing key")
    return base64.b64encode(key.sign(payload, ec.ECDSA(hashes.SHA256()))).decode("ascii")


def verify(key_path, payload, signature):
    key = serialization.load_pem_public_key(key_path.read_bytes())
    if not isinstance(key, ec.EllipticCurvePublicKey) or not isinstance(key.curve, ec.SECP256R1):
        raise ValueError("Expected an ECDSA P-256 verification key")
    try:
        key.verify(base64.b64decode(signature, validate=True), payload, ec.ECDSA(hashes.SHA256()))
    except (InvalidSignature, binascii.Error) as exc:
        raise ValueError("Invalid firmware signature") from exc


def validate_package(manifest, image, public_key):
    verify(public_key, canonical_manifest(manifest), manifest.get("signature", ""))
    if len(image) != manifest["size"] or hashlib.sha256(image).hexdigest() != manifest["sha256"]:
        raise ValueError("Firmware digest or size mismatch")
    # ESP image magic and ESP32-S3 chip ID in the official image header.
    if image[0] != 0xE9 or image[12:14] != b"\x09\x00":
        raise ValueError("Invalid ESP32-S3 application image header")
