import hmac
import io

from flask import Blueprint, current_app, jsonify, request, send_file

from .audio_processing import parse_wav
from .diagnostics import service_status
from .errors import ServiceError
from .vision import validate_jpeg

api = Blueprint("api", __name__)


@api.before_request
def authenticate():
    if request.path.startswith("/api/"):
        token = current_app.config["SETTINGS"].device_token
        provided = request.headers.get("X-Device-Token", "")
        if token and not hmac.compare_digest(provided.encode(), token.encode()):
            raise ServiceError("UNAUTHORIZED", "Valid X-Device-Token required", 401)


@api.get("/healthz")
def health():
    return jsonify(service="InspectPin AI", status="alive", api_version=1)


@api.get("/api/v1/status")
def status():
    return jsonify(service_status(current_app.config["SETTINGS"], current_app.extensions["jobs"], current_app.extensions["services"]))


@api.post("/api/v1/jobs/<kind>")
def upload(kind):
    s = current_app.config["SETTINGS"]
    if kind not in ("voice", "image"):
        raise ServiceError("NOT_FOUND", "Unknown upload type", 404)
    expected = "audio/wav" if kind == "voice" else "image/jpeg"
    if request.mimetype != expected:
        raise ServiceError("CONTENT_TYPE", f"Use Content-Type: {expected}", 415)
    limit = s.max_voice_bytes if kind == "voice" else s.max_image_bytes
    if request.content_length is not None and request.content_length > limit:
        raise ServiceError("UPLOAD_TOO_LARGE", "Upload exceeds size limit", 413)
    data = request.stream.read(limit + 1)
    if len(data) > limit:
        raise ServiceError("UPLOAD_TOO_LARGE", "Upload exceeds size limit", 413)
    if kind == "voice":
        info = parse_wav(data)
        if info["duration_seconds"] > 30:
            raise ServiceError("AUDIO_TOO_LONG", "Maximum recording duration is 30 seconds")
    else:
        validate_jpeg(data)
    question = request.args.get("question", "Describe the visible equipment. State uncertainty.")
    if not 1 <= len(question) <= 500:
        raise ServiceError("INVALID_QUESTION", "Question length must be 1..500 characters", 400)
    job = current_app.extensions["jobs"].submit(kind, data, question)
    response = jsonify(job)
    response.status_code = 202
    response.headers["Location"] = "/api/v1/jobs/" + job["id"]
    return response


@api.get("/api/v1/jobs/<ident>")
def job_status(ident):
    return jsonify(current_app.extensions["jobs"].get(ident))


@api.get("/api/v1/jobs/<ident>/audio")
def audio(ident):
    data = current_app.extensions["jobs"].audio(ident)
    return send_file(io.BytesIO(data), mimetype="audio/wav", download_name=f"{ident}.wav", max_age=0)
