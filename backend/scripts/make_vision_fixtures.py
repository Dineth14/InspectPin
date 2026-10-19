"""Generate deterministic artificial label fixtures; these are not real equipment."""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main():
    root = Path("tests/fixtures")
    root.mkdir(parents=True, exist_ok=True)
    for name, voltage, current in [("synthetic_nameplate_a", "230 V", "4.2 A"),
                                    ("synthetic_nameplate_b", "400 V", "2.4 A")]:
        image = Image.new("RGB", (1024, 768), "white")
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default(size=42)
        lines = ["INSPECTPIN TEST FIXTURE", "ARTIFICIAL MOTOR NAMEPLATE", "MODEL: DEMO-123",
                 "VOLTAGE: " + voltage, "CURRENT: " + current, "POWER: 0.75 kW", "FREQUENCY: 50 Hz", "NOT REAL EQUIPMENT"]
        for i, line in enumerate(lines):
            draw.text((32, 35 + i*85), line, font=font, fill="black")
        image.save(root / (name + ".jpg"), "JPEG", quality=95)
        (root / (name + ".json")).write_text(json.dumps({"synthetic": True, "model": "DEMO-123", "voltage": voltage,
             "current": current, "power": "0.75 kW", "frequency": "50 Hz"}, indent=2), encoding="utf-8")
        print(root / (name + ".jpg"))


if __name__ == "__main__":
    main()
