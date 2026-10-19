import hmac
import io

from flask import Blueprint, current_app, jsonify, request, send_file

from .audio_processing import parse_wav
from .conversations import validate_device_id
from .diagnostics import service_status
from .errors import ServiceError
from .vision import validate_jpeg

api = Blueprint("api", __name__)


def device_id(required=False):
    value = request.headers.get("X-Device-ID")
    if value is None:
        if required:
            raise ServiceError("DEVICE_ID_REQUIRED", "Send a stable X-Device-ID for conversation/image requests", 400)
        return None
    return validate_device_id(value)


def body_bytes(content_type, limit):
    if request.mimetype != content_type:
        raise ServiceError("CONTENT_TYPE", f"Use Content-Type: {content_type}", 415)
    if request.content_length is not None and request.content_length > limit:
        raise ServiceError("UPLOAD_TOO_LARGE", "Upload exceeds size limit", 413)
    data = request.stream.read(limit + 1)
    if len(data) > limit:
        raise ServiceError("UPLOAD_TOO_LARGE", "Upload exceeds size limit", 413)
    if request.content_length is not None and len(data) != request.content_length:
        raise ServiceError("INCOMPLETE_UPLOAD", "Request body is incomplete", 400)
    return data


def accepted(job):
    response = jsonify(job)
    response.status_code = 202
    response.headers["Location"] = "/api/v1/jobs/" + job["id"]
    return response


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
    return jsonify(service_status(current_app.config["SETTINGS"], current_app.extensions["jobs"], current_app.extensions["services"], device_id()))


@api.post("/api/v1/images")
def image_upload():
    owner = device_id(required=True)
    s = current_app.config["SETTINGS"]
    data = body_bytes("image/jpeg", s.vision_max_image_bytes)
    info = validate_jpeg(data)
    result = current_app.extensions["jobs"].conversations.upload(owner, data, info)
    response = jsonify(result)
    response.status_code = 201
    response.headers["Location"] = "/api/v1/images/" + result["image_id"]
    return response


@api.get("/api/v1/images/<ident>")
def image_info(ident):
    return jsonify(current_app.extensions["jobs"].conversations.image(device_id(True), ident))


@api.get("/api/v1/images/<ident>/content")
def image_content(ident):
    data = current_app.extensions["jobs"].conversations.image(device_id(True), ident, content=True)
    return send_file(io.BytesIO(data), mimetype="image/jpeg", download_name=f"{ident}.jpg", max_age=0)


@api.route("/api/v1/session", methods=["GET", "DELETE"])
def session():
    owner = device_id(True)
    conversations = current_app.extensions["jobs"].conversations
    return jsonify(conversations.clear(owner) if request.method == "DELETE" else conversations.status(owner))


@api.post("/api/v1/jobs/question")
def question_job():
    owner = device_id(True)
    if request.mimetype != "application/json":
        raise ServiceError("CONTENT_TYPE", "Use Content-Type: application/json", 415)
    data = request.get_json()
    if not isinstance(data, dict) or not isinstance(data.get("question"), str) or not 1 <= len(data["question"].strip()) <= 500:
        raise ServiceError("INVALID_QUESTION", "Question must be a nonempty string of at most 500 characters", 400)
    for field in ("image_id", "context_id"):
        if data.get(field) is not None and (not isinstance(data[field], str) or len(data[field]) != 32):
            raise ServiceError("INVALID_CONTEXT", f"{field} must be a 32-character ID", 400)
    return accepted(current_app.extensions["jobs"].submit(
        "question", request.get_data(), data["question"].strip(), owner, data.get("image_id"), data.get("context_id")))


@api.post("/api/v1/jobs/<kind>")
def upload(kind):
    s = current_app.config["SETTINGS"]
    if kind not in ("voice", "image"):
        raise ServiceError("NOT_FOUND", "Unknown upload type", 404)
    expected = "audio/wav" if kind == "voice" else "image/jpeg"
    limit = s.max_voice_bytes if kind == "voice" else s.max_image_bytes
    data = body_bytes(expected, limit)
    if kind == "voice":
        info = parse_wav(data)
        if info["duration_seconds"] > 30:
            raise ServiceError("AUDIO_TOO_LONG", "Maximum recording duration is 30 seconds")
    else:
        validate_jpeg(data)
    question = request.args.get("question", "Describe the visible equipment. State uncertainty.")
    if not 1 <= len(question) <= 500:
        raise ServiceError("INVALID_QUESTION", "Question length must be 1..500 characters", 400)
    owner = device_id()
    image_id = request.args.get("image_id")
    context_id = request.args.get("context_id")
    if kind == "image" and (image_id or context_id):
        raise ServiceError("INVALID_CONTEXT", "Use /images then /jobs/voice or /jobs/question for conversation", 400)
    return accepted(current_app.extensions["jobs"].submit(kind, data, question, owner, image_id, context_id))


@api.get("/api/v1/jobs/<ident>")
def job_status(ident):
    return jsonify(current_app.extensions["jobs"].get(ident, device_id()))


@api.get("/api/v1/jobs/<ident>/audio")
def audio(ident):
    data = current_app.extensions["jobs"].audio(ident, device_id())
    return send_file(io.BytesIO(data), mimetype="audio/wav", download_name=f"{ident}.wav", max_age=0)
