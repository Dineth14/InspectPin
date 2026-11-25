"""Provision and serve the private LAN TLS endpoint used by InspectPin OTA."""
import argparse
from datetime import datetime, timedelta, timezone
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from ipaddress import IPv4Address
import os
from pathlib import Path
import ssl

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

ROOT = Path(__file__).resolve().parents[1]


def prepare(folder, address, port):
    if folder.resolve().is_relative_to(ROOT):
        raise ValueError("Keep the TLS private key outside the repository")
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    if any((folder / f).exists() for f in ("lan-ca.pem", "lan-cert.pem", "lan-key.pem")):
        raise ValueError("Use an empty directory for a new LAN trust anchor")
    ca_key = ec.generate_private_key(ec.SECP256R1())
    key = ec.generate_private_key(ec.SECP256R1())
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "InspectPin local firmware CA")])
    server_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, str(address))])
    now = datetime.now(timezone.utc)

    def builder(subject, issuer, public):
        return (x509.CertificateBuilder().subject_name(subject).issuer_name(issuer).public_key(public)
                .serial_number(x509.random_serial_number()).not_valid_before(now - timedelta(minutes=10))
                .not_valid_after(now + timedelta(days=365)))

    ca = (builder(ca_name, ca_name, ca_key.public_key())
          .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
          .sign(ca_key, hashes.SHA256()))
    server = (builder(server_name, ca_name, key.public_key())
              .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
              .add_extension(x509.SubjectAlternativeName([x509.IPAddress(address)]), critical=False)
              .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
              .sign(ca_key, hashes.SHA256()))
    public = ca.public_bytes(serialization.Encoding.PEM)
    (folder / "lan-ca.pem").write_bytes(public)
    (folder / "lan-cert.pem").write_bytes(server.public_bytes(serialization.Encoding.PEM))
    with os.fdopen(os.open(folder / "lan-key.pem", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as out:
        out.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                    serialization.NoEncryption()))
    (ROOT / "firmware/InspectPinAI/ota_transport.local.h").write_text(
        '#pragma once\n'
        f'constexpr char otaReceiverOrigin[]="https://{address}:{port}";\n'
        f'constexpr char otaReceiverCa[]=R"pem({public.decode("ascii")})pem";\n', encoding="ascii")


def serve(folder, address, port):
    class Handler(BaseHTTPRequestHandler):
        def forward(self):
            if not self.path.startswith("/api/v1/device/firmware/"):
                self.send_error(404)
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
            except ValueError:
                self.send_error(400)
                return
            if not 0 <= length <= 4096 or self.headers.get("Transfer-Encoding"):
                self.send_error(413)
                return
            headers = {name: self.headers[name] for name in
                       ("X-Device-ID", "X-Device-Token", "Content-Type") if name in self.headers}
            headers["X-Forwarded-Proto"] = "https"
            upstream = HTTPConnection("127.0.0.1", 5000, timeout=15)
            try:
                upstream.request(self.command, self.path, self.rfile.read(length) if length else None, headers)
                reply = upstream.getresponse()
                self.send_response(reply.status)
                for name in ("Content-Length", "Content-Type", "Cache-Control"):
                    if value := reply.getheader(name):
                        self.send_header(name, value)
                self.end_headers()
                while chunk := reply.read(65536):
                    self.wfile.write(chunk)
            finally:
                upstream.close()

        do_GET = do_POST = forward

    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.minimum_version = ssl.TLSVersion.TLSv1_2
    tls.load_cert_chain(folder / "lan-cert.pem", folder / "lan-key.pem")
    with ThreadingHTTPServer((str(address), port), Handler) as server:
        server.socket = tls.wrap_socket(server.socket, server_side=True)
        print(f"InspectPin OTA delivery on https://{address}:{port}", flush=True)
        server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "serve"))
    parser.add_argument("--dir", type=Path, required=True)
    parser.add_argument("--address", type=IPv4Address, required=True)
    parser.add_argument("--port", type=int, default=5443)
    args = parser.parse_args()
    (prepare if args.action == "prepare" else serve)(args.dir, args.address, args.port)


if __name__ == "__main__":
    main()
