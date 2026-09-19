from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


INK = (91, 47, 37, 255)
PAPER = (255, 249, 235, 255)
ORANGE = (232, 95, 45, 255)
GOLD = (248, 187, 62, 255)
PINK = (239, 126, 142, 255)


def pick_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/simsun.ttc"),
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                return ImageFont.truetype(str(candidate), size)
            except OSError:
                continue
    return ImageFont.load_default()


def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for character in text:
        candidate = current + character
        if current and font.getlength(candidate) > max_width:
            lines.append(current)
            current = character
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def draw_bubble(
    image: Image.Image,
    text: str,
    center_x: int,
    y: int,
    max_text_width: int = 286,
) -> int:
    if not text:
        return y

    font = pick_font(17)
    lines = wrap_text(text, font, max_text_width)
    line_height = 25
    text_width = max(font.getlength(line) for line in lines)
    text_height = line_height * len(lines)
    pad_x, pad_y = 18, 13
    width = int(text_width + pad_x * 2 + 12)
    height = max(52, int(text_height + pad_y * 2))
    left = center_x - width // 2
    right = left + width
    top = y
    bottom = top + height

    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle(
        (left, top, right, bottom),
        radius=17,
        fill=PAPER,
        outline=INK,
        width=3,
    )
    draw.rounded_rectangle(
        (left + 6, top + 6, right - 6, bottom - 6),
        radius=12,
        outline=(244, 195, 112, 255),
        width=1,
    )
    tail_x = max(left + 28, min(center_x + 18, right - 25))
    draw.polygon(
        (
            (tail_x - 10, bottom - 2),
            (tail_x + 5, bottom + 17),
            (tail_x + 16, bottom - 2),
        ),
        fill=PAPER,
        outline=INK,
    )
    draw.line((tail_x - 9, bottom - 1, tail_x + 15, bottom - 1), fill=PAPER, width=4)
    draw.ellipse((left + 10, top + 10, left + 18, top + 18), fill=GOLD)
    draw.ellipse((left + 15, top + 10, left + 23, top + 18), fill=ORANGE)

    text_y = top + (height - text_height) // 2 - 1
    for line in lines:
        x = center_x - font.getlength(line) / 2
        draw.text((x, text_y), line, fill=INK, font=font)
        text_y += line_height
    return bottom + 18


def draw_sparkle(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    size: int,
    color: tuple[int, int, int, int],
) -> None:
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
    )


def draw_accessory(image: Image.Image, action: str, frame: int, variant: int = 0) -> None:
    draw = ImageDraw.Draw(image, "RGBA")

    if action == "study":
        draw.polygon(
            ((75, 451), (156, 438), (159, 487), (75, 490)),
            fill=(255, 252, 239, 255),
            outline=INK,
        )
        draw.polygon(
            ((159, 438), (240, 451), (240, 490), (159, 487)),
            fill=(245, 237, 211, 255),
            outline=INK,
        )
        draw.line((159, 444, 159, 486), fill=INK, width=2)
        for index in range(3):
            draw.line(
                (89 + index * 3, 457 + index * 8, 140 + index, 452 + index * 8),
                fill=(180, 139, 108, 255),
                width=2,
            )
            draw.line(
                (175, 452 + index * 9, 225 - index * 2, 458 + index * 8),
                fill=(180, 139, 108, 255),
                width=2,
            )
    elif action == "eat":
        if variant == 0:
            draw.ellipse((255, 431, 365, 490), fill=(73, 50, 41, 255), outline=INK, width=3)
            draw.ellipse((246, 423, 374, 462), fill=(246, 245, 232, 255), outline=INK, width=3)
            draw.chord((263, 426, 357, 458), 180, 360, fill=(255, 255, 250, 255), outline=INK, width=2)
            draw.line((294, 385, 307, 429), fill=(116, 66, 43, 255), width=4)
            draw.line((314, 382, 319, 428), fill=(116, 66, 43, 255), width=4)
            for offset in (0, 14):
                draw.arc((291 + offset, 375, 310 + offset, 408), 85, 270, fill=(238, 238, 226, 230), width=2)
        else:
            draw.ellipse((247, 438, 367, 484), fill=(255, 245, 224, 255), outline=INK, width=3)
            for index, color in enumerate(((248, 164, 91, 255), (240, 220, 194, 255), (244, 133, 94, 255))):
                x = 276 + index * 31
                draw.ellipse((x - 14, 410 - index * 2, x + 14, 438 - index * 2), fill=color, outline=INK, width=2)
            draw.line((267, 403, 330, 446), fill=(126, 75, 49, 255), width=4)
    elif action == "drink":
        if variant == 0:
            draw.rounded_rectangle((270, 405, 356, 479), radius=10, fill=(247, 249, 242, 255), outline=INK, width=3)
            draw.ellipse((275, 402, 351, 423), fill=(229, 199, 155, 255), outline=INK, width=3)
            draw.arc((341, 429, 379, 466), 270, 90, fill=INK, width=5)
            draw.arc((261, 385, 286, 408), 80, 260, fill=(234, 241, 231, 210), width=2)
        else:
            draw.polygon(((276, 395), (352, 395), (343, 482), (285, 482)), fill=(140, 207, 230, 235), outline=INK)
            draw.rectangle((286, 379, 338, 402), fill=(246, 216, 147, 255), outline=INK, width=2)
            draw.line((342, 382, 369, 428), fill=(238, 124, 92, 255), width=5)
    elif action == "daydream":
        drift = math.sin(frame * 0.06) * 4
        draw.ellipse((292, 235 + drift, 330, 257 + drift), fill=(255, 248, 232, 255), outline=INK, width=2)
        draw.ellipse((321, 220 + drift, 349, 237 + drift), fill=(255, 248, 232, 255), outline=INK, width=2)
        draw.ellipse((343, 234 + drift, 366, 249 + drift), fill=(255, 248, 232, 255), outline=INK, width=2)
        draw_sparkle(draw, 315, 205 + drift, 8, GOLD)
        draw_sparkle(draw, 365, 211 + drift, 6, ORANGE)
    elif action == "sleep":
        drift = abs(math.sin(frame * 0.03)) * 4
        draw.text((309, 265 - drift), "Z", font=pick_font(25, bold=True), fill=INK)
        draw.text((333, 235 - drift), "Z", font=pick_font(20, bold=True), fill=ORANGE)
        draw.text((351, 212 - drift), "Z", font=pick_font(16, bold=True), fill=GOLD)
        if variant == 1:
            draw.rounded_rectangle((252, 409, 369, 480), radius=28, fill=(158, 184, 226, 145), outline=(92, 109, 151, 200), width=3)
    elif action == "cheer":
        colors = (ORANGE, GOLD, (81, 147, 184, 255), (238, 138, 112, 255))
        for index in range(18):
            angle = index * math.tau / 18 + frame * 0.012
            radius = 151 + (index % 3) * 11
            x = int(200 + math.cos(angle) * radius)
            y = int(303 + math.sin(angle) * radius)
            size = 3 + index % 3
            draw.rectangle((x, y, x + size * 2, y + size), fill=colors[index % len(colors)])
    elif action == "welcome":
        pulse = 2 + int((math.sin(frame * 0.08) + 1) * 2)
        draw_sparkle(draw, 315, 323, 10 + pulse, GOLD)
        draw_sparkle(draw, 78, 356, 7 + pulse, ORANGE)
    elif action == "stretch":
        pulse = 4 + int((math.sin(frame * 0.07) + 1) * 3)
        draw_sparkle(draw, 69, 322, 8 + pulse, GOLD)
        draw_sparkle(draw, 334, 319, 8 + pulse, ORANGE)
        draw.arc((105, 283, 299, 398), 205, 335, fill=(249, 191, 72, 190), width=3)
    elif action == "look_fireworks":
        for index, (x, y, size, color) in enumerate(
            (
                (326, 206, 23, GOLD),
                (351, 173, 12, ORANGE),
                (289, 171, 9, (97, 174, 216, 230)),
            )
        ):
            drift = math.sin(frame * 0.05 + index) * 3
            for angle_index in range(8):
                angle = angle_index * math.tau / 8
                draw.line(
                    (
                        x + drift,
                        y,
                        x + drift + math.cos(angle) * size,
                        y + math.sin(angle) * size,
                    ),
                    fill=color,
                    width=2,
                )
    elif action == "shy":
        pulse = 2 + int((math.sin(frame * 0.08) + 1) * 2)
        draw.ellipse((152, 346, 188, 365), fill=(246, 144, 153, 125))
        draw.ellipse((264, 346, 300, 365), fill=(246, 144, 153, 125))
        draw_sparkle(draw, 330, 242, 8 + pulse, PINK)


def draw_blink(image: Image.Image, pose_name: str, frame: int) -> None:
    if pose_name != "idle":
        return
    draw = ImageDraw.Draw(image, "RGBA")
    y = 351 + math.sin(frame * 0.1) * 0.5
    for center_x in (183, 254):
        draw.arc(
            (center_x - 12, y - 5, center_x + 12, y + 5),
            195,
            345,
            fill=(112, 63, 47, 245),
            width=2,
        )


def draw_hover_hint(image: Image.Image, region: str, frame: int) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    pulse = 3 + int((math.sin(frame * 0.09) + 1) * 2)
    if region == "head":
        draw_sparkle(draw, 280, 245, 7 + pulse, (255, 211, 92, 215))
        draw_sparkle(draw, 306, 267, 5 + pulse, (244, 126, 70, 210))
    elif region == "hair":
        draw_sparkle(draw, 116, 205, 6 + pulse, (255, 210, 91, 215))
        draw_sparkle(draw, 286, 179, 7 + pulse, (241, 131, 88, 215))
    elif region == "face":
        draw_sparkle(draw, 215, 344, 5 + pulse, (240, 126, 145, 220))
        draw_sparkle(draw, 258, 337, 5 + pulse, (240, 126, 145, 220))
    elif region == "accessory":
        draw_sparkle(draw, 82, 369, 6 + pulse, (105, 181, 220, 220))
    elif region == "outfit":
        draw_sparkle(draw, 202, 444, 6 + pulse, (249, 180, 72, 220))
    elif region == "hand":
        draw_sparkle(draw, 337, 388, 7 + pulse, (255, 208, 75, 220))
