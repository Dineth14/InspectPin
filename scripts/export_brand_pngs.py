"""Export deterministic PNG previews of the reconstructed brand assets."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "branding" / "png"


def font(size: int):
    candidates = [
        Path("C:/Windows/Fonts/segoeuib.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default(size=size)


def wordmark(path: Path, width: int, light: bool = False) -> None:
    height = round(width * 124 / 540)
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    scale = width / 540
    face = font(round(64 * scale))
    x, y = round(8 * scale), round(10 * scale)
    colors = ("#081525", "#007F8A") if light else ("#F7FAFF", "#00DFE8")
    for text, color in (("Inspect", colors[0]), ("Pin", colors[1]), (" AI", colors[0])):
        draw.text((x, y), text, font=face, fill=color, stroke_width=0)
        x += round(draw.textlength(text, font=face) - 2 * scale)
    draw.rounded_rectangle((round(8 * scale), round(99 * scale), round(80 * scale), round(105 * scale)),
                           radius=max(1, round(3 * scale)), fill=colors[1])
    image.save(path)


def icon(path: Path, size: int) -> None:
    image = Image.new("RGB", (size, size), "#081525")
    draw = ImageDraw.Draw(image)
    margin = round(size * .18)
    draw.rounded_rectangle((margin, margin, size-margin, size-margin), radius=round(size*.07),
                           fill="#102036", outline="#29415B", width=max(2, size//64))
    face = font(round(size*.34))
    draw.text((round(size*.27), round(size*.30)), "I", font=face, fill="#F7FAFF")
    draw.text((round(size*.43), round(size*.30)), "P", font=face, fill="#00DFE8")
    draw.rounded_rectangle((round(size*.27), round(size*.70), round(size*.47), round(size*.725)),
                           radius=round(size*.01), fill="#00DFE8")
    image.save(path)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for width in (540, 1080):
        wordmark(OUT / f"inspectpin-wordmark-dark-{width}.png", width)
        wordmark(OUT / f"inspectpin-wordmark-light-{width}.png", width, True)
    for size in (192, 512, 1024):
        icon(OUT / f"inspectpin-icon-{size}.png", size)
    print(f"Exported 7 PNG files to {OUT}")


if __name__ == "__main__":
    main()
