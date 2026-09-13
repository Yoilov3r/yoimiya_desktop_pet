from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


INPUTS = {
    "idle": "fa5e9e590cb5653ae47ef06c80d1a852_6964121008511609520.jpg",
    "cheer": "7b653a2b2d7886c2c5e54907da5202b5_4287803002730244481.png",
    "welcome": "b2ff1c07f49091531d09aa0465224c47_7485700441489103118.gif",
    "wink": "32ecfa5faba46f89a8acbfa48f6d0d43_6942308241108952269.jpg",
}


def edge_seeds(image: Image.Image, step: int = 20) -> list[tuple[int, int]]:
    width, height = image.size
    return (
        [(x, 1) for x in range(0, width, step)]
        + [(x, height - 2) for x in range(0, width, step)]
        + [(1, y) for y in range(0, height, step)]
        + [(width - 2, y) for y in range(0, height, step)]
    )


def remove_background(image: Image.Image, mode: str) -> Image.Image:
    rgba = image.convert("RGBA")
    keyed = image.convert("RGB")
    magic = (255, 0, 255)
    draw = ImageDraw.Draw(keyed)

    if mode == "yellow-card":
        for seed in edge_seeds(image, step=16):
            ImageDraw.floodfill(keyed, seed, magic, thresh=38)
        width, height = image.size
        for seed in ((width // 2, 92), (width // 2, 130), (width // 4, 125), (3 * width // 4, 125)):
            ImageDraw.floodfill(keyed, seed, magic, thresh=74)
    else:
        for seed in edge_seeds(image, step=12):
            ImageDraw.floodfill(keyed, seed, magic, thresh=48)

    keyed_pixels = np.asarray(keyed)
    background = np.all(keyed_pixels == np.asarray(magic, dtype=np.uint8), axis=2)
    alpha = np.where(background, 0, 255).astype(np.uint8)
    alpha_image = Image.fromarray(alpha, mode="L").filter(ImageFilter.GaussianBlur(0.35))
    rgba.putalpha(alpha_image)

    bbox = rgba.getchannel("A").point(lambda value: 255 if value > 16 else 0).getbbox()
    if bbox:
        rgba = rgba.crop(bbox)

    padding = max(12, int(max(rgba.size) * 0.035))
    canvas = Image.new("RGBA", (rgba.width + padding * 2, rgba.height + padding * 2), (0, 0, 0, 0))
    canvas.alpha_composite(rgba, (padding, padding))
    return canvas


def fit_asset(image: Image.Image, max_size: int = 1400) -> Image.Image:
    ratio = min(1.0, max_size / max(image.size))
    if ratio >= 1.0:
        return image.copy()
    return image.resize(
        (max(1, round(image.width * ratio)), max(1, round(image.height * ratio))),
        Image.Resampling.LANCZOS,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for key, filename in INPUTS.items():
        source = args.input_dir / filename
        if not source.exists():
            raise FileNotFoundError(source)
        mode = "yellow-card" if key == "cheer" else "white"
        prepared = fit_asset(remove_background(Image.open(source), mode))
        destination = args.output_dir / f"{key}.png"
        prepared.save(destination, optimize=True)
        print(f"{destination.name}: {prepared.width}x{prepared.height}")

    icon_source = args.output_dir / "idle.png"
    icon = Image.open(icon_source).convert("RGBA")
    icon.thumbnail((256, 256), Image.Resampling.LANCZOS)
    icon_canvas = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    icon_canvas.alpha_composite(icon, ((256 - icon.width) // 2, (256 - icon.height) // 2))
    icon_canvas.save(args.output_dir / "pet.ico", sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])


if __name__ == "__main__":
    main()
