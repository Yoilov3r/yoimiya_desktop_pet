from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


PROJECT = Path(__file__).resolve().parents[1]
POSE_DIR = PROJECT / "assets" / "poses"
OUTPUT_DIR = PROJECT / "assets" / "action_variants"

ACTION_SOURCES = {
    "idle": ("idle", "idle_mirror"),
    "study": ("wink", "wink_mirror"),
    "eat": ("welcome", "welcome_mirror"),
    "drink": ("welcome_mirror", "welcome"),
    "daydream": ("idle", "idle_mirror"),
    "cheer": ("welcome", "welcome_mirror"),
    "welcome": ("welcome", "welcome_mirror"),
    "sleep": ("wink", "wink_mirror"),
    "stretch": ("welcome", "welcome_mirror"),
    "shy": ("idle_close", "idle_mirror"),
    "look_fireworks": ("wink", "wink_mirror"),
}

ACCENTS = {
    "study": ((103, 192, 221), (245, 188, 80)),
    "eat": ((247, 166, 79), (240, 115, 81)),
    "drink": ((102, 190, 225), (244, 223, 173)),
    "sleep": ((135, 165, 222), (177, 192, 235)),
    "cheer": ((240, 111, 74), (250, 201, 75)),
    "daydream": ((244, 186, 77), (132, 188, 220)),
    "stretch": ((248, 185, 72), (237, 124, 91)),
    "shy": ((240, 132, 151), (250, 186, 132)),
    "look_fireworks": ((250, 181, 59), (102, 179, 219)),
    "welcome": ((236, 112, 76), (250, 196, 77)),
    "idle": ((247, 188, 76), (238, 125, 92)),
}


def sparkle(draw: ImageDraw.ImageDraw, x: int, y: int, size: int, color) -> None:
    draw.polygon(
        (
            (x, y - size),
            (x + size * 0.28, y - size * 0.28),
            (x + size, y),
            (x + size * 0.28, y + size * 0.28),
            (x, y + size),
            (x - size * 0.28, y + size * 0.28),
            (x - size, y),
            (x - size * 0.28, y - size * 0.28),
        ),
        fill=(*color, 205),
    )


def fit_canvas(source: Image.Image, angle: float, scale: float) -> Image.Image:
    rotated = source.rotate(
        angle,
        resample=Image.Resampling.BICUBIC,
        expand=True,
    )
    if scale != 1.0:
        rotated = rotated.resize(
            (round(rotated.width * scale), round(rotated.height * scale)),
            Image.Resampling.LANCZOS,
        )
    canvas = Image.new("RGBA", source.size, (0, 0, 0, 0))
    x = (canvas.width - rotated.width) // 2
    y = canvas.height - rotated.height
    canvas.alpha_composite(rotated, (x, y))
    return canvas


def add_accents(image: Image.Image, action: str, variant: int) -> Image.Image:
    color_a, color_b = ACCENTS.get(action, ACCENTS["idle"])
    color = color_a if variant == 0 else color_b
    draw = ImageDraw.Draw(image, "RGBA")
    width, height = image.size
    points = (
        (0.16, 0.24, 13),
        (0.78, 0.19, 9),
        (0.87, 0.43, 7),
        (0.25, 0.48, 6),
    )
    for index, (px, py, size) in enumerate(points):
        x = round(width * px)
        y = round(height * py)
        sparkle(draw, x, y, size + variant * 2, color if index % 2 == 0 else color_b)

    if action == "sleep":
        draw.ellipse(
            (width * 0.62, height * 0.16, width * 0.78, height * 0.26),
            fill=(255, 249, 233, 175),
            outline=(112, 84, 111, 180),
            width=4,
        )
        draw.text(
            (width * 0.66, height * 0.17),
            "Z",
            fill=(105, 73, 104, 230),
            stroke_width=2,
            stroke_fill=(255, 255, 255, 200),
        )
    elif action == "drink":
        for offset in range(3):
            x = width * (0.72 + offset * 0.045)
            y = height * (0.26 + offset * 0.03)
            draw.ellipse(
                (x - 7, y - 12, x + 7, y + 12),
                fill=(137, 211, 238, 185),
                outline=(80, 129, 165, 170),
                width=3,
            )
    return image


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for action, sources in ACTION_SOURCES.items():
        for variant, source_name in enumerate(sources):
            source = Image.open(POSE_DIR / f"{source_name}.png").convert("RGBA")
            angle = -2.8 if variant == 0 else 2.5
            scale = 0.975 if variant == 0 else 0.99
            prepared = fit_canvas(source, angle, scale)
            if variant == 0:
                prepared = ImageEnhance.Color(prepared).enhance(1.03)
            else:
                prepared = prepared.filter(
                    ImageFilter.UnsharpMask(radius=0.8, percent=48, threshold=3)
                )
            prepared = add_accents(prepared, action, variant)
            prepared.save(OUTPUT_DIR / f"{action}_{variant + 1}.png", optimize=True)
    print(f"Generated {len(ACTION_SOURCES) * 2} action variant images.")


if __name__ == "__main__":
    main()
