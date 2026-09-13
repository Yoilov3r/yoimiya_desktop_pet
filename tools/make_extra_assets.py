from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw


PROJECT = Path(__file__).resolve().parents[1]
POSE_DIR = PROJECT / "assets" / "poses"
EFFECT_DIR = PROJECT / "assets" / "effects"
INK = (91, 47, 37, 255)
ORANGE = (232, 95, 45, 255)
GOLD = (248, 187, 62, 255)
PINK = (239, 126, 142, 255)
SKY = (111, 184, 220, 255)


def star(draw: ImageDraw.ImageDraw, x: float, y: float, size: float, color) -> None:
    draw.polygon(
        (
            (x, y - size),
            (x + size * 0.25, y - size * 0.25),
            (x + size, y),
            (x + size * 0.25, y + size * 0.25),
            (x, y + size),
            (x - size * 0.25, y + size * 0.25),
            (x - size, y),
            (x - size * 0.25, y - size * 0.25),
        ),
        fill=color,
        outline=INK,
        width=4,
    )


def heart(draw: ImageDraw.ImageDraw, x: float, y: float, size: float, color) -> None:
    draw.ellipse((x - size, y - size * 0.8, x, y + size * 0.15), fill=color)
    draw.ellipse((x, y - size * 0.8, x + size, y + size * 0.15), fill=color)
    draw.polygon(((x - size, y - size * 0.05), (x + size, y - size * 0.05), (x, y + size)), fill=color)
    draw.arc((x - size, y - size * 0.8, x, y + size * 0.15), 180, 360, fill=INK, width=4)
    draw.arc((x, y - size * 0.8, x + size, y + size * 0.15), 180, 360, fill=INK, width=4)


def blank() -> Image.Image:
    return Image.new("RGBA", (512, 512), (0, 0, 0, 0))


def make_effects() -> None:
    EFFECT_DIR.mkdir(parents=True, exist_ok=True)

    image = blank()
    draw = ImageDraw.Draw(image, "RGBA")
    for x, y, size, color in (
        (164, 176, 47, PINK),
        (322, 132, 54, PINK),
        (350, 318, 43, (247, 165, 157, 255)),
    ):
        heart(draw, x, y, size, color)
    image.save(EFFECT_DIR / "heart_blush.png")

    image = blank()
    draw = ImageDraw.Draw(image, "RGBA")
    for x, y, size, color in (
        (256, 250, 86, GOLD),
        (128, 166, 38, ORANGE),
        (378, 154, 31, SKY),
        (392, 344, 42, GOLD),
    ):
        star(draw, x, y, size, color)
    image.save(EFFECT_DIR / "spark_cluster.png")

    image = blank()
    draw = ImageDraw.Draw(image, "RGBA")
    for x, y in ((160, 312), (244, 238), (330, 174)):
        draw.ellipse((x - 25, y + 42, x + 25, y + 72), fill=INK)
        draw.rectangle((x - 8, y - 15, x + 8, y + 45), fill=INK)
        draw.polygon(((x + 6, y + 35), (x + 70, y + 8), (x + 70, y + 28), (x + 6, y + 55)), fill=INK)
    image.save(EFFECT_DIR / "music_notes.png")

    image = blank()
    draw = ImageDraw.Draw(image, "RGBA")
    draw.polygon(((256, 72), (344, 256), (286, 246), (324, 402), (178, 310), (238, 302), (184, 178)), fill=SKY)
    draw.line(((256, 85), (246, 410)), fill=(235, 249, 255, 255), width=20)
    draw.polygon(((256, 72), (344, 256), (286, 246), (324, 402), (178, 310), (238, 302), (184, 178)), outline=INK, width=8)
    image.save(EFFECT_DIR / "sweat_drop.png")

    image = blank()
    draw = ImageDraw.Draw(image, "RGBA")
    draw.line((256, 90, 256, 430), fill=ORANGE, width=20)
    for angle in (35, 90, 145, 215, 270, 325):
        radians = math.radians(angle)
        x = 256 + math.cos(radians) * 120
        y = 256 + math.sin(radians) * 120
        draw.line((256, 256, x, y), fill=ORANGE, width=18)
    draw.ellipse((232, 232, 280, 280), fill=GOLD, outline=INK, width=5)
    image.save(EFFECT_DIR / "anger_mark.png")

    image = blank()
    draw = ImageDraw.Draw(image, "RGBA")
    draw.arc((124, 106, 388, 398), 205, 500, fill=GOLD, width=28)
    draw.line((184, 194, 184, 356), fill=GOLD, width=24)
    draw.ellipse((152, 340, 216, 404), fill=GOLD, outline=INK, width=6)
    draw.polygon(((152, 375), (105, 454), (172, 430)), fill=GOLD, outline=INK, width=5)
    image.save(EFFECT_DIR / "question_mark.png")

    image = blank()
    draw = ImageDraw.Draw(image, "RGBA")
    for index in range(12):
        angle = index * math.tau / 12
        inner = 72
        outer = 175 + (index % 3) * 18
        x1 = 256 + math.cos(angle) * inner
        y1 = 256 + math.sin(angle) * inner
        x2 = 256 + math.cos(angle) * outer
        y2 = 256 + math.sin(angle) * outer
        draw.line((x1, y1, x2, y2), fill=(255, 179, 67, 235), width=13)
        draw.ellipse((x2 - 11, y2 - 11, x2 + 11, y2 + 11), fill=(255, 229, 120, 255), outline=INK, width=4)
    draw.ellipse((218, 218, 294, 294), fill=(255, 239, 175, 255), outline=INK, width=7)
    image.save(EFFECT_DIR / "firework.png")

    image = blank()
    draw = ImageDraw.Draw(image, "RGBA")
    for index in range(8):
        angle = index * math.tau / 8
        x = 256 + math.cos(angle) * 128
        y = 256 + math.sin(angle) * 128
        draw.ellipse((x - 54, y - 34, x + 54, y + 34), fill=(255, 179, 88, 235), outline=INK, width=5)
    draw.ellipse((185, 185, 327, 327), fill=GOLD, outline=INK, width=8)
    image.save(EFFECT_DIR / "flower_burst.png")


def make_pose_variants() -> None:
    for name in ("idle", "cheer", "welcome", "wink"):
        source = Image.open(POSE_DIR / f"{name}.png").convert("RGBA")
        mirrored = source.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        mirrored.save(POSE_DIR / f"{name}_mirror.png", optimize=True)

    idle = Image.open(POSE_DIR / "idle.png").convert("RGBA")
    bbox = idle.getchannel("A").getbbox()
    if bbox:
        idle = idle.crop(bbox)
    close_height = max(1, round(idle.height * 0.66))
    close = idle.crop((0, 0, idle.width, close_height))
    close.save(POSE_DIR / "idle_close.png", optimize=True)


if __name__ == "__main__":
    make_effects()
    make_pose_variants()
    print("Generated expression effects and pose variants.")
