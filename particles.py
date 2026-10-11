from __future__ import annotations

import math
import random
from dataclasses import dataclass

from PIL import Image, ImageDraw


PALETTE = (
    (244, 104, 53, 255),
    (252, 187, 61, 255),
    (228, 71, 93, 255),
    (87, 164, 201, 255),
    (255, 235, 145, 255),
)


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    size: float
    color: tuple[int, int, int, int]
    gravity: float = 8.0
    shape: str = "dot"
    rotation: float = 0.0
    spin: float = 0.0
    text: str = ""


class ParticleSystem:
    def __init__(self) -> None:
        self.particles: list[Particle] = []

    def emit(
        self,
        x: float,
        y: float,
        count: int = 16,
        power: float = 75.0,
        shape: str = "dot",
        colors: tuple[tuple[int, int, int, int], ...] | None = None,
        gravity: float | None = None,
    ) -> None:
        for _ in range(count):
            angle = random.uniform(-math.pi, math.pi)
            speed = random.uniform(power * 0.35, power)
            life = random.uniform(0.55, 1.25)
            self.particles.append(
                Particle(
                    x=x,
                    y=y,
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed - random.uniform(10, 35),
                    life=life,
                    max_life=life,
                    size=random.uniform(2.0, 5.0),
                    color=random.choice(colors or PALETTE),
                    gravity=(
                        gravity
                        if gravity is not None
                        else random.uniform(55, 105)
                    ),
                    shape=shape,
                    spin=random.uniform(-6.0, 6.0),
                )
            )

    def emit_effect(self, effect: str, x: float, y: float, intensity: float = 1.0) -> None:
        if effect == "hearts":
            self.emit(
                x,
                y,
                6,
                42,
                shape="heart",
                colors=((238, 118, 143, 235), (245, 157, 166, 220)),
                gravity=-14,
            )
        elif effect == "stars":
            self.emit(
                x,
                y,
                10,
                62,
                shape="star",
                colors=((250, 190, 65, 245), (245, 123, 82, 225)),
                gravity=8,
            )
        elif effect == "sparkles":
            self.emit(
                x,
                y,
                8,
                48,
                shape="spark",
                colors=((253, 214, 96, 235), (111, 184, 220, 220)),
                gravity=0,
            )
        elif effect == "crumbs":
            self.emit(
                x,
                y,
                9,
                34,
                shape="crumb",
                colors=((218, 158, 93, 235), (174, 108, 65, 220)),
                gravity=90,
            )
        elif effect == "steam":
            self.emit(
                x,
                y,
                5,
                18,
                shape="cloud",
                colors=((245, 242, 229, 155),),
                gravity=-22,
            )
        elif effect == "water":
            self.emit(
                x,
                y,
                8,
                42,
                shape="drop",
                colors=((115, 194, 228, 225), (185, 228, 244, 220)),
                gravity=86,
            )
        elif effect == "zzz":
            self.emit(
                x,
                y,
                3,
                8,
                shape="text",
                colors=((112, 87, 124, 220),),
                gravity=-10,
            )
        elif effect == "confetti":
            self.emit(
                x,
                y,
                max(8, round(18 * intensity)),
                90,
                shape="rect",
                colors=PALETTE,
                gravity=58,
            )
        elif effect == "question":
            self.emit(
                x,
                y,
                4,
                24,
                shape="text_question",
                colors=((218, 153, 54, 230),),
                gravity=-7,
            )
        elif effect == "sweat":
            self.emit(
                x,
                y,
                5,
                34,
                shape="drop",
                colors=((116, 190, 224, 225),),
                gravity=72,
            )
        elif effect == "anger":
            self.emit(
                x,
                y,
                7,
                50,
                shape="anger",
                colors=((238, 102, 74, 230),),
                gravity=10,
            )
        else:
            self.emit(x, y, 10, 55)

    def update(self, seconds: float) -> None:
        alive: list[Particle] = []
        for particle in self.particles:
            particle.life -= seconds
            if particle.life <= 0:
                continue
            particle.vy += particle.gravity * seconds
            particle.x += particle.vx * seconds
            particle.y += particle.vy * seconds
            particle.rotation += particle.spin * seconds
            alive.append(particle)
        self.particles = alive[-360:]

    def draw(self, image: Image.Image, scale: float = 1.0) -> None:
        if not self.particles:
            return
        draw = ImageDraw.Draw(image, "RGBA")
        for particle in self.particles:
            fade = max(0.0, min(1.0, particle.life / particle.max_life))
            color = (*particle.color[:3], round(particle.color[3] * fade))
            x = particle.x * scale
            y = particle.y * scale
            size = max(1.0, particle.size * scale * (0.7 + fade * 0.3))
            if particle.shape == "heart":
                draw.ellipse(
                    (x - size, y - size * 0.9, x, y + size * 0.2),
                    fill=color,
                )
                draw.ellipse(
                    (x, y - size * 0.9, x + size, y + size * 0.2),
                    fill=color,
                )
                draw.polygon(
                    ((x - size, y), (x + size, y), (x, y + size * 1.25)),
                    fill=color,
                )
            elif particle.shape == "star":
                points = []
                for index in range(10):
                    angle = -math.pi / 2 + index * math.pi / 5
                    radius = size if index % 2 == 0 else size * 0.42
                    points.append(
                        (x + math.cos(angle) * radius, y + math.sin(angle) * radius)
                    )
                draw.polygon(points, fill=color)
            elif particle.shape == "spark":
                draw.line((x - size, y, x + size, y), fill=color, width=max(1, round(scale)))
                draw.line((x, y - size, x, y + size), fill=color, width=max(1, round(scale)))
            elif particle.shape == "crumb":
                draw.rectangle((x - size * 0.6, y - size * 0.4, x + size * 0.6, y + size * 0.4), fill=color)
            elif particle.shape == "cloud":
                draw.ellipse((x - size, y - size * 0.55, x + size, y + size * 0.55), fill=color)
            elif particle.shape == "drop":
                draw.polygon(
                    ((x, y - size * 1.4), (x + size * 0.8, y + size * 0.45), (x, y + size), (x - size * 0.8, y + size * 0.45)),
                    fill=color,
                )
            elif particle.shape == "rect":
                points = []
                for px, py in (
                    (-size, -size * 0.45),
                    (size, -size * 0.45),
                    (size, size * 0.45),
                    (-size, size * 0.45),
                ):
                    rotated_x = px * math.cos(particle.rotation) - py * math.sin(particle.rotation)
                    rotated_y = px * math.sin(particle.rotation) + py * math.cos(particle.rotation)
                    points.append((x + rotated_x, y + rotated_y))
                draw.polygon(points, fill=color)
            elif particle.shape == "text":
                draw.text((x, y), random.choice(("Z", "z")), fill=color)
            elif particle.shape == "text_question":
                draw.text((x, y), "?", fill=color)
            elif particle.shape == "anger":
                draw.line((x - size, y, x + size, y), fill=color, width=max(1, round(scale * 2)))
                draw.line((x, y - size, x, y + size), fill=color, width=max(1, round(scale * 2)))
            else:
                draw.ellipse((x - size, y - size, x + size, y + size), fill=color)


def draw_seasonal_ambient(image: Image.Image, frame: int, scale: float = 1.0) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    width = round(400 * scale)
    height = round(530 * scale)
    month = __import__("datetime").datetime.now().month
    if month in (3, 4, 5):
        color = (239, 142, 158, 125)
        shape = "petal"
    elif month in (6, 7, 8):
        color = (250, 184, 55, 115)
        shape = "spark"
    elif month in (9, 10, 11):
        color = (214, 126, 66, 120)
        shape = "leaf"
    else:
        color = (205, 231, 244, 125)
        shape = "snow"

    points = (
        (0.10, 0.18),
        (0.18, 0.54),
        (0.88, 0.22),
        (0.76, 0.60),
        (0.94, 0.72),
        (0.08, 0.82),
    )
    for index, (px, py) in enumerate(points):
        drift_x = math.sin(frame * 0.018 + index * 1.7) * 9
        drift_y = math.sin(frame * 0.012 + index * 2.1) * 6
        x = px * width + drift_x * scale
        y = py * height + drift_y * scale
        size = (4 + index % 3) * scale
        if shape == "petal":
            draw.ellipse((x - size, y - size * 0.55, x + size, y + size * 0.55), fill=color)
        elif shape == "leaf":
            draw.polygon(
                ((x, y - size), (x + size, y), (x, y + size), (x - size, y)),
                fill=color,
            )
        elif shape == "spark":
            draw.line((x - size, y, x + size, y), fill=color, width=max(1, round(scale)))
            draw.line((x, y - size, x, y + size), fill=color, width=max(1, round(scale)))
        else:
            draw.ellipse((x - size * 0.55, y - size * 0.55, x + size * 0.55, y + size * 0.55), fill=color)
