import io
import struct
import time
import wave
from dataclasses import replace

import pytest
from PIL import Image

from inspectpin.audio_processing import tone
from inspectpin.errors import ServiceError
from inspectpin.recordings import metadata
from test_product_api import account, paired


def silent_clip():
    frame = io.BytesIO()
    Image.new("RGB", (320, 240), "blue").save(frame, "JPEG")
    jpeg = frame.getvalue()
    head = bytearray(224)
    head[:4], head[8:12], head[108:116] = b"RIFF", b"AVI ", b"vidsMJPG"
    head[212:216], head[220:224] = b"LIST", b"movi"
    for offset, value in [(48, 1), (56, 1), (64, 320), (68, 240), (128, 1), (132, 5)]:
        struct.pack_into("<I", head, offset, value)
    chunk = b"00dc" + struct.pack("<I", len(jpeg)) + jpeg + bytes(len(jpeg) % 2)
    struct.pack_into("<I", head, 216, len(chunk)+4)
    head.extend(chunk + b"idx1" + struct.pack("<I4sIII", 16, b"00dc", 16, 4, len(jpeg)))
    struct.pack_into("<I", head, 4, len(head)-8)
    return bytes(head)


@pytest.mark.parametrize("video", [False, True])
def test_recording_round_trip(factory, video):
    client = factory().test_client()
    owner, other = account(client), account(client, "other@example.test")
    device = paired(client, owner)
    mime = "video/x-msvideo" if video else "audio/wav"
    original = silent_clip() if video else tone()
    headers = {**device, "Idempotency-Key": "sample.avi" if video else "sample_note.wav"}
    def post(data):
        return client.post("/api/v1/device/recordings", data=data, content_type=mime, headers=headers)
    assert post(original[:-4]).status_code >= 400
    receipt = post(original)
    assert receipt.status_code == 201
    assert post(original).json == receipt.json
    ident = receipt.json["inspection_id"]
    item = client.get("/api/v1/inspections/"+ident, headers=owner).json
    uri = "/api/v1/media/"+item["media"][0]["id"]
    assert client.get(uri, headers=other).status_code == 404
    assert client.get(uri, headers=owner).data == original
    note = "/api/v1/inspections/"+ident+"/note"
    assert client.patch(note, headers=other, json={"note":"no"}).status_code == 404
    assert client.patch(note, headers=owner, json={"note":"checked"}).json["note"] == "checked"
    assert client.get(note[:-5]+"/report", headers=owner).data.startswith(b"%PDF")
    if video:
        assert client.get(uri+"/preview", headers=other).status_code == 404
        assert client.get(uri+"/preview", headers=owner).data.startswith(b"GIF")
    else:
        assert post(tone(seconds=2)).status_code == 409


def test_offline_configuration_is_enforced(factory):
    app = factory()
    client = app.test_client()
    owner = account(client)
    device = paired(client, owner)
    body = {"mode":"offline", "llm_provider":"ollama", "llm_model":"local-test", "vision_provider":"none"}
    assert client.patch("/api/v1/settings/ai", headers=owner, json=body).json["mode"] == "offline"
    assert client.get("/api/v1/session", headers=device).json["offline_recording"]
    with pytest.raises(ServiceError, match="AI processing paused"):
        app.extensions["ai_configuration"].for_device(device["X-Device-ID"])


def test_production_rejects_mock_and_damaged_video(settings):
    with pytest.raises(ValueError, match="Production"):
        replace(settings, deployment_mode="production").validate()
    with pytest.raises(ServiceError):
        metadata(b"invalid", "video/x-msvideo")


def test_full_length_audio_and_limit(factory):
    client = factory().test_client()
    owner = account(client)
    headers = {**paired(client, owner), "Idempotency-Key": "full_note.wav"}
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as output:
        output.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        output.writeframes(bytes(60 * 32000))
    original = buffer.getvalue()
    result = client.post("/api/v1/device/recordings", headers=headers, content_type="audio/wav", data=original)
    assert result.status_code == 201
    item = client.get("/api/v1/inspections/"+result.json["inspection_id"], headers=owner).json
    assert item["processing_metadata"]["duration_seconds"] == 60
    assert client.get("/api/v1/media/"+item["media"][0]["id"], headers=owner).data == original
    assert client.post("/api/v1/device/recordings", headers=headers, content_type="audio/wav",
                       data=original+b"\x00\x00").status_code == 413


def test_protected_mp4_playback_and_range(factory):
    av = pytest.importorskip("av")
    client = factory().test_client()
    owner, other = account(client), account(client, "second@example.test")
    headers = {**paired(client, owner), "Idempotency-Key": "clip.avi"}
    original = silent_clip()
    receipt = client.post("/api/v1/device/recordings", headers=headers, content_type="video/x-msvideo", data=original)
    item = client.get("/api/v1/inspections/"+receipt.json["inspection_id"], headers=owner).json
    uri = "/api/v1/media/"+item["media"][0]["id"]
    assert client.get(uri+"/playback", headers=other).status_code == 404
    first = client.get(uri+"/playback", headers=owner)
    assert first.status_code == 202
    deadline = time.monotonic()+35
    while time.monotonic() < deadline:
        response = client.get(uri+"/playback", headers=owner)
        if response.status_code != 202:
            break
        time.sleep(.1)
    assert response.status_code == 200
    with av.open(io.BytesIO(response.data)) as movie:
        assert len(movie.streams.video) == 1 and not movie.streams.audio
        assert len(list(movie.decode(video=0))) == 1
    part = client.get(uri+"/playback", headers={**owner, "Range": "bytes=0-15"})
    assert part.status_code == 206 and part.data == response.data[:16]
    assert client.get(uri+"/playback", headers=other).status_code == 404
    assert client.get(uri, headers=owner).data == original
