from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FW = ROOT / "firmware/InspectPinAI"


def read(name):
    return (FW / name).read_text(encoding="utf-8")


def test_video_has_separate_conservative_profile_and_streaming_writer():
    profile = read("video_profile.h")
    writer = read("avi_writer.cpp")
    recorder = read("video_recorder.cpp")
    assert "FRAMESIZE_QVGA" in profile
    assert "targetFps=5" in profile
    assert 'writeFourCC("RIFF")' in writer
    assert 'writeFourCC("movi")' in writer
    assert 'writeFourCC("idx1")' in writer
    assert "appendJpeg" in writer
    assert ".idx.tmp" in writer
    assert "frame->buf" in recorder
    assert "frame->len" in recorder
    assert "returnVideoFrame(frame)" in recorder
    assert "minimumFreeBytes" in recorder
    assert "maximumDurationMs" in recorder


def test_video_does_not_allocate_whole_file_and_recovery_is_explicit():
    writer = read("avi_writer.cpp")
    recorder = read("video_recorder.cpp")
    assert "std::vector" not in writer
    assert "malloc" not in writer
    assert "ps_malloc" not in writer
    assert ".avi.part" in recorder
    assert ".incomplete" in recorder
    assert "recoverIncomplete" in recorder


def test_photo_profile_remains_svga_and_video_is_explicitly_separate():
    camera = read("camera_manager.cpp")
    photo = camera.split("bool captureJpeg(const String &path)", 1)[1].split("bool diagnoseCamera", 1)[0]
    assert "fb->width == 800 && fb->height == 600" in photo
    assert "VideoProfile::frameSize" not in photo
    assert "beginVideoCamera" in camera
