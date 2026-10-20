from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
PROFILE = (ROOT / "firmware/InspectPinAI/camera_profile.h").read_text(encoding="utf-8")
CAMERA = (ROOT / "firmware/InspectPinAI/camera_manager.cpp").read_text(encoding="utf-8")
API = (ROOT / "firmware/InspectPinAI/api_client.cpp").read_text(encoding="utf-8")


def macro(name: str) -> int:
    match = re.search(rf"^#define {name} (-?\d+)$", PROFILE, re.MULTILINE)
    assert match, f"missing numeric camera profile constant {name}"
    return int(match.group(1))


def test_approved_camera_profile_and_capture_invariants():
    assert macro("IP_CAMERA_XCLK_HZ") == 20_000_000
    assert macro("IP_CAMERA_JPEG_QUALITY") == 12
    assert macro("IP_CAMERA_BRIGHTNESS") == 1
    assert macro("IP_CAMERA_CONTRAST") == 0
    assert macro("IP_CAMERA_SATURATION") == -2
    assert macro("IP_CAMERA_SHARPNESS") == 1
    assert macro("IP_CAMERA_DENOISE") == 5
    assert macro("IP_CAMERA_AE_LEVEL") == 0
    assert "c.frame_size = FRAMESIZE_SVGA" in CAMERA
    assert "fb->width == 800 && fb->height == 600" in CAMERA
    assert "FRAMESIZE_QVGA" not in CAMERA
    assert "CAMERA_FB_IN_PSRAM" in CAMERA
    capture = CAMERA.split("bool captureJpeg(const String &path)", 1)[1]
    assert "ensureCameraProfileActive(sensor)" in capture
    assert capture.index("ensureCameraProfileActive(sensor)") < capture.index(
        "camera_fb_t *fb = esp_camera_fb_get()"
    )


def test_profile_is_centralized_verified_and_upload_remains_streamed():
    assert "bool applyOptimizedCameraProfile(sensor_t *sensor)" in CAMERA
    assert "verifyProfile(sensor, p, false)" in CAMERA
    assert "original tuned value unavailable" in CAMERA
    for setter in (
        "set_framesize", "set_quality", "set_brightness", "set_contrast",
        "set_saturation", "set_sharpness", "set_denoise", "set_ae_level",
        "set_whitebal", "set_awb_gain", "set_exposure_ctrl", "set_gain_ctrl",
        "set_raw_gma", "set_lenc", "set_aec2",
    ):
        assert f"sensor->{setter}" in CAMERA
    assert 'http.sendRequest("POST",&f,f.size())' in API
