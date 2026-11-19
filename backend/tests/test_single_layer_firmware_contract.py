from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIRMWARE = ROOT / "firmware" / "InspectPinAI"


def source(name: str) -> str:
    return (FIRMWARE / name).read_text(encoding="utf-8")


def test_single_layer_gpio_contract_is_exact():
    profile = source("hardware_profile.h")
    expected = {
        "speakerBclkGpio = 1": "D0 BCLK",
        "speakerLrclkGpio = 2": "D1 LRC",
        "speakerDataGpio = 4": "D3 DIN",
        "askButtonGpio = 5": "D4 ASK",
        "ampOffGpio = 6": "D5 amplifier shutdown",
        "photoButtonGpio = 44": "D7 PHOTO",
        "buttonPinMode = INPUT": "external PCB pull-ups",
    }
    for declaration, purpose in expected.items():
        assert declaration in profile, purpose


def test_sd_camera_microphone_and_removed_features_are_protected():
    config = source("config.h")
    profile_config = source("config.single_layer.example.h")
    assert "sdCS = 21, sdSCK = 7, sdMISO = 8, sdMOSI = 9" in config
    assert "micClock = 42, micData = 41" in config
    assert "!IP_PCF8574_ENABLED && !IP_BATTERY_ENABLED" in config
    assert "!IP_CHARGE_DECODER_ENABLED" in config
    assert "#define IP_PCF8574_ENABLED false" in profile_config
    assert "#define IP_BATTERY_ENABLED false" in profile_config


def test_amplifier_polarity_and_sleep_wake_contract():
    audio = source("audio_player.cpp")
    power = source("power_manager.cpp")
    profile_config = source("config.single_layer.example.h")
    assert "digitalWrite(Config::ampOff,HIGH)" in audio
    assert "digitalWrite(Config::ampOff,on?LOW:HIGH)" in audio
    assert "Amp::shutdownForSleep();" in power
    assert "ESP_EXT1_WAKEUP_ANY_LOW" in power
    assert "#define IP_IDLE_TIMEOUT_MS 300000UL" in profile_config

