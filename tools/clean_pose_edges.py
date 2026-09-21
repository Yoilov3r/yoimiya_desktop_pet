from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageFilter


PROJECT = Path(__file__).resolve().parents[1]
TARGET_DIRS = (
    PROJECT / "assets" / "poses",
    PROJECT / "assets" / "action_variants",
)


def clean(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    alpha = image.getchannel("A").filter(ImageFilter.MinFilter(3))
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.28))
    alpha = alpha.point(
        lambda value: 0 if value < 20 else (255 if value > 245 else value)
    )
    cleaned = image.copy()
    cleaned.putalpha(alpha)
    bbox = alpha.point(lambda value: 255 if value > 12 else 0).getbbox()
    if bbox:
        cleaned = cleaned.crop(bbox)
    padding = 12
    canvas = Image.new(
        "RGBA",
        (cleaned.width + padding * 2, cleaned.height + padding * 2),
        (0, 0, 0, 0),
    )
    canvas.alpha_composite(cleaned, (padding, padding))
    return canvas


def main() -> None:
    count = 0
    for directory in TARGET_DIRS:
        for path in directory.glob("*.png"):
            if path.name == "pet.ico":
                continue
            cleaned = clean(Image.open(path))
            cleaned.save(path, optimize=True)
            count += 1
    print(f"Cleaned {count} pose images.")


if __name__ == "__main__":
    main()
