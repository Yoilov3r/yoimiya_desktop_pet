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


class ParticleSystem:
    def __init__(self) -> None:
        self.particles: list[Particle] = []

    def emit(self, x: float, y: float, count: int = 16, power: float = 75.0) -> None:
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
                    color=random.choice(PALETTE),
                    gravity=random.uniform(55, 105),
                )
            )

    def update(self, seconds: float) -> None:
        alive: list[Particle] = []
        for particle in self.particles:
            particle.life -= seconds
            if particle.life <= 0:
                continue
            particle.vy += particle.gravity * seconds
            particle.x += particle.vx * seconds
            particle.y += particle.vy * seconds
            alive.append(particle)
        self.particles = alive[-240:]

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
