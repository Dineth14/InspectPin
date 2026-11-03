"""Versioned account, device, inspection, media and live-event API."""
from __future__ import annotations

import io
import json
import re
import time
import textwrap

from flask import Blueprint, Response, current_app, jsonify, request, send_file
from PIL import Image, ImageDraw, ImageFont, ImageOps

from .errors import ServiceError
from .vision import validate_jpeg


product = Blueprint("product", __name__)


def store():
    return current_app.extensions["product_store"]


def json_body() -> dict:
    if request.mimetype != "application/json":
        raise ServiceError("CONTENT_TYPE", "Use Content-Type: application/json", 415)
    value = request.get_json(silent=True)
    if not isinstance(value, dict):
        raise ServiceError("INVALID_JSON", "Request body must be a JSON object", 400)
    return value


def bearer() -> str:
    value = request.headers.get("Authorization", "")
    if not value.startswith("Bearer "):
        raise ServiceError("UNAUTHORIZED", "Bearer access token required", 401)
    return value[7:]


def user_id() -> str:
    return store().authenticate_user(bearer())


def device_auth() -> dict:
    ident = request.headers.get("X-Device-ID", "")
    token = request.headers.get("X-Device-Token", "")
    return store().authenticate_device(ident, token)


@product.get("/api/v1/health")
def health():
    return jsonify(status="alive", service="InspectPin AI", api_version="v1")


@product.get("/api/v1/ready")
def ready():
    current_app.extensions["product_store"].db.execute("SELECT 1").fetchone()
    return jsonify(status="ready", database="ok")


@product.post("/api/v1/auth/register")
def register():
    data = json_body()
    result = store().register(str(data.get("name", "")), str(data.get("email", "")),
                              str(data.get("password", "")))
    return jsonify(result), 201


@product.post("/api/v1/auth/login")
def login():
    data = json_body()
    return jsonify(store().login(str(data.get("email", "")), str(data.get("password", ""))))


@product.post("/api/v1/auth/refresh")
def refresh():
    old = bearer()
    ident = store().authenticate_user(old)
    with store().lock, store().db:
        store().logout(old)
        return jsonify(store()._issue_session(ident))


@product.post("/api/v1/auth/logout")
def logout():
    token = bearer()
    store().authenticate_user(token)
    store().logout(token)
    return "", 204


@product.get("/api/v1/auth/me")
def me():
    return jsonify(store().user(user_id()))


@product.post("/api/v1/devices/pair")
def pair():
    owner, data = user_id(), json_body()
    required = ("device_id", "name", "model", "hardware_revision", "firmware_version")
    if any(not isinstance(data.get(key), str) for key in required):
        raise ServiceError("INVALID_DEVICE", "All device identity fields are required", 400)
    return jsonify(store().pair_device(owner, *(data[key] for key in required))), 201


@product.get("/api/v1/devices")
def devices():
    return jsonify(items=store().devices(user_id()))


@product.get("/api/v1/devices/<ident>")
def device(ident):
    return jsonify(store().device(user_id(), ident))


@product.get("/api/v1/devices/<ident>/status")
def device_status(ident):
    return jsonify(store().device(user_id(), ident))


@product.patch("/api/v1/devices/<ident>")
def rename_device(ident):
    owner, data = user_id(), json_body()
    name = data.get("name")
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
        raise ServiceError("INVALID_NAME", "Device name must contain 1..80 characters", 400)
    store().device(owner, ident)
    with store().lock, store().db:
        store().db.execute("UPDATE devices SET name=? WHERE id=?", (name.strip(), ident))
    return jsonify(store().device(owner, ident))


@product.delete("/api/v1/devices/<ident>")
def unpair_device(ident):
    owner = user_id()
    store().device(owner, ident)
    with store().lock, store().db:
        store().db.execute("UPDATE devices SET revoked_at=?,online=0 WHERE id=?", (time.time(), ident))
        store().audit(owner, "device.revoke", "device", ident)
    return "", 204


@product.post("/api/v1/devices/<ident>/commands")
def issue_command(ident):
    owner, data = user_id(), json_body()
    return jsonify(store().create_command(owner, ident, str(data.get("type", "")),
                                          data.get("payload") if isinstance(data.get("payload"), dict) else {},
                                          int(data.get("ttl_seconds", 120)))), 201


@product.post("/api/v1/device/heartbeat")
def heartbeat():
    device = device_auth()
    return jsonify(store().heartbeat(device["id"], json_body()))


@product.get("/api/v1/device/commands")
def poll_commands():
    device = device_auth()
    return jsonify(items=store().pending_commands(device["id"]))


@product.post("/api/v1/device/commands/<ident>/ack")
def ack_command(ident):
    device, data = device_auth(), json_body()
    return jsonify(store().acknowledge_command(device["id"], ident, str(data.get("status", "")),
                                               data.get("result") if isinstance(data.get("result"), dict) else {}))


@product.post("/api/v1/uploads/init")
def init_upload():
    device, data = device_auth(), json_body()
    result = store().init_upload(
        device["owner_id"], device["id"], str(data.get("kind", "")),
        str(data.get("content_type", "")), int(data.get("total_bytes", 0)),
        str(data.get("sha256", "")), int(data.get("chunk_size", 65536)),
        request.headers.get("Idempotency-Key", ""),
    )
    return jsonify(result), 201


@product.put("/api/v1/uploads/<ident>/chunks/<int:index>")
def upload_chunk(ident, index):
    device = device_auth()
    limit = 512 * 1024
    data = request.stream.read(limit + 1)
    if len(data) > limit:
        raise ServiceError("CHUNK_TOO_LARGE", "Chunk exceeds 512 KiB", 413)
    return jsonify(store().upload_chunk(device["id"], ident, index, data))


@product.post("/api/v1/uploads/<ident>/complete")
def complete_upload(ident):
    device = device_auth()
    return jsonify(store().complete_upload(device["id"], ident))


@product.post("/api/v1/inspections")
def create_inspection():
    owner, data = user_id(), json_body()
    device_id = data.get("device_id")
    if device_id is not None and not isinstance(device_id, str):
        raise ServiceError("INVALID_DEVICE", "device_id must be a string", 400)
    return jsonify(store().create_inspection(owner, device_id, str(data.get("title", "Inspection")),
                                             bool(data.get("simulated", False)))), 201


@product.get("/api/v1/inspections")
def inspections():
    owner = user_id()
    try:
        limit = max(1, min(100, int(request.args.get("limit", 20))))
        offset = max(0, int(request.args.get("offset", 0)))
    except ValueError as exc:
        raise ServiceError("INVALID_PAGINATION", "limit and offset must be integers", 400) from exc
    return jsonify(store().inspections(owner, limit, offset, request.args.get("status")))


@product.get("/api/v1/inspections/<ident>")
def inspection(ident):
    return jsonify(store().inspection(user_id(), ident))


@product.delete("/api/v1/inspections/<ident>")
def delete_inspection(ident):
    store().delete_inspection(user_id(), ident)
    return "", 204


@product.post("/api/v1/inspections/<ident>/analyze")
def analyze_inspection(ident):
    owner, data = user_id(), json_body()
    question = data.get("question", "Describe only visible components and possible visual concerns. State uncertainty.")
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 500:
        raise ServiceError("INVALID_QUESTION", "Question must contain 1..500 characters", 400)
    job = current_app.extensions["product_jobs"].submit_analysis(
        owner, ident, question.strip(), request.headers.get("Idempotency-Key"))
    return jsonify(job), 202


@product.get("/api/v1/processing-jobs/<ident>")
def product_job(ident):
    return jsonify(store().processing_job(user_id(), ident))


@product.post("/api/v1/inspections/<ident>/questions")
def ask_inspection(ident):
    owner, data = user_id(), json_body()
    question = data.get("question")
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 500:
        raise ServiceError("INVALID_QUESTION", "Question must contain 1..500 characters", 400)
    job = current_app.extensions["product_jobs"].submit_assistant(
        owner, ident, question.strip(), request.headers.get("Idempotency-Key"))
    return jsonify(job), 202


@product.post("/api/v1/inspections/<ident>/media")
def upload_media(ident):
    owner = user_id()
    content_type = request.mimetype
    if content_type not in {"image/jpeg", "audio/wav"}:
        raise ServiceError("CONTENT_TYPE", "Only image/jpeg and audio/wav are accepted", 415)
    limit = current_app.config["SETTINGS"].vision_max_image_bytes if content_type == "image/jpeg" else current_app.config["SETTINGS"].max_voice_bytes
    data = request.stream.read(limit + 1)
    if not data or len(data) > limit:
        raise ServiceError("UPLOAD_SIZE", "Media is empty or exceeds its configured limit", 413)
    if content_type == "image/jpeg":
        validate_jpeg(data)
    kind = "image" if content_type == "image/jpeg" else "question_audio"
    return jsonify(store().save_media(owner, ident, kind, content_type, data)), 201


@product.get("/api/v1/media/<ident>")
def media(ident):
    data, content_type = store().media(user_id(), ident, content=True)
    suffix = "jpg" if content_type == "image/jpeg" else "wav"
    return send_file(io.BytesIO(data), mimetype=content_type, download_name=f"{ident}.{suffix}", max_age=0)


def _pdf_escape(text: str) -> str:
    return re.sub(r"([\\()])", r"\\\1", text).replace("\r", " ").replace("\n", " ")


def simple_pdf(lines: list[str]) -> bytes:
    """Build a deterministic one-page text PDF without an extra dependency."""
    y = 800
    commands = ["BT", "/F1 11 Tf"]
    for line in lines[:45]:
        commands.extend((f"50 {y} Td", f"({_pdf_escape(line[:110])}) Tj", f"-50 {-y + (y-17)} Td"))
        y -= 17
    commands.append("ET")
    stream = "\n".join(commands).encode("latin-1", "replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(out))
        out.extend(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(out)
    out.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    out.extend(b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:]))
    out.extend(f"trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(out)


def inspection_pdf(item: dict, image_bytes: bytes | None) -> bytes:
    """Render a stable report layout with the original image when available."""
    try:
        page = Image.new("RGB", (1240, 1754), "white")
        draw, font = ImageDraw.Draw(page), ImageFont.load_default(size=24)
        draw.rectangle((0, 0, 1240, 150), fill="#071018")
        draw.text((60, 48), "INSPECTPIN AI  /  INSPECTION REPORT", fill="#32bfae", font=font)
        y = 190
        for line in (f"Inspection: {item['id']}", f"Device: {item['device_id'] or 'manual upload'}",
                     f"Status: {item['status']}", f"Created: {item['created_at']}"):
            draw.text((60, y), line, fill="#16232b", font=font)
            y += 36
        if image_bytes:
            with Image.open(io.BytesIO(image_bytes)) as source:
                evidence = ImageOps.contain(source.convert("RGB"), (1120, 560), Image.Resampling.LANCZOS)
            page.paste(evidence, ((1240 - evidence.width) // 2, y + 18))
            y += evidence.height + 60
        draw.text((60, y), "SUMMARY", fill="#087e73", font=font)
        y += 42
        content = [item["summary"] or "No analysis is available.", "", "VISIBLE FINDINGS"]
        content.extend(
            finding.get("description", str(finding)) if isinstance(finding, dict) else str(finding)
            for finding in item["findings"]
        )
        content.extend(("", "Advisory visual analysis only. It does not replace electrical testing",
                        "or a qualified safety inspection."))
        for paragraph in content:
            for line in textwrap.wrap(paragraph, 88) or [""]:
                if y > 1680:
                    break
                draw.text((60, y), line, fill="#16232b", font=font)
                y += 34
        output = io.BytesIO()
        page.save(output, format="PDF", resolution=150.0, title="InspectPin AI Inspection Report")
        return output.getvalue()
    except (OSError, ValueError):
        lines = ["InspectPin AI Inspection Report", f"Inspection ID: {item['id']}",
                 item["summary"] or "No analysis is available."]
        return simple_pdf(lines)


@product.get("/api/v1/inspections/<ident>/report")
def report(ident):
    item = store().inspection(user_id(), ident)
    image_bytes = None
    if item.get("image_media_id"):
        image_bytes, _ = store().media(item["owner_id"], item["image_media_id"], content=True)
    return send_file(io.BytesIO(inspection_pdf(item, image_bytes)), mimetype="application/pdf",
                     download_name=f"inspectpin-{ident}.pdf", as_attachment=True, max_age=0)


@product.get("/api/v1/events")
def events():
    owner = user_id()

    def generate():
        payload = {"type": "snapshot", "devices": store().devices(owner),
                   "inspections": store().inspections(owner, 5, 0)["items"], "timestamp": time.time()}
        yield "event: snapshot\ndata: " + json.dumps(payload, separators=(",", ":")) + "\n\n"

    return Response(generate(), mimetype="text/event-stream", headers={"X-Accel-Buffering": "no"})


@product.get("/api/v1/openapi.json")
def openapi():
    """Machine-readable contract summary; detailed examples live in docs/API.md."""
    paths = {
        path: {method: {"summary": summary}}
        for path, method, summary in [
            ("/api/v1/auth/register", "post", "Register user"),
            ("/api/v1/auth/login", "post", "Create session"),
            ("/api/v1/devices/pair", "post", "Pair device"),
            ("/api/v1/device/heartbeat", "post", "Report device telemetry"),
            ("/api/v1/device/commands", "get", "Poll device commands"),
            ("/api/v1/uploads/init", "post", "Initialize resumable upload"),
            ("/api/v1/uploads/{id}/chunks/{index}", "put", "Store upload chunk"),
            ("/api/v1/uploads/{id}/complete", "post", "Verify and complete upload"),
            ("/api/v1/inspections", "get", "List owned inspections"),
            ("/api/v1/inspections/{id}", "get", "Get owned inspection"),
            ("/api/v1/inspections/{id}/analyze", "post", "Queue vision analysis"),
            ("/api/v1/inspections/{id}/report", "get", "Download PDF report"),
        ]
    }
    return jsonify(openapi="3.1.0", info={"title": "InspectPin AI API", "version": "1.0.0"}, paths=paths)
