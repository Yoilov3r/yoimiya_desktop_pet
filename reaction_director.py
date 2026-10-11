from __future__ import annotations

import math
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class ReactionMotion:
    offset_x: float = 0.0
    offset_y: float = 0.0
    angle: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    shake_x: float = 0.0


REACTIONS = {
    "face": (0.42, -5.0, -2.0, 2.8, 0.035, "hearts"),
    "hair": (0.48, 2.5, -2.0, -3.8, 0.018, "sparkles"),
    "hand": (0.38, 0.0, -8.0, 1.8, 0.045, "stars"),
    "body": (0.40, 0.0, -5.0, 1.2, 0.030, "stars"),
    "accessory": (0.44, 3.0, -2.0, 2.0, 0.022, "sparkles"),
    "outfit": (0.36, -2.0, -3.0, -1.5, 0.022, "question"),
    "rapid": (0.42, 0.0, 0.0, 5.5, 0.030, "anger"),
    "drag": (0.50, 0.0, 0.0, 6.5, 0.040, "sweat"),
}


class ReactionDirector:
    def __init__(self) -> None:
        self.kind = ""
        self.started_at = 0.0
        self.duration = 0.4
        self.strength = 0.0
        self.angle_strength = 0.0
        self.squash = 0.0
        self.effect = None

    def trigger(self, kind: str) -> str | None:
        if kind not in REACTIONS:
            return None
        (
            self.duration,
            self.strength,
            _unused_y,
            self.angle_strength,
            self.squash,
            self.effect,
        ) = REACTIONS[kind]
        self.kind = kind
        self.started_at = time.monotonic()
        return self.effect

    def sample(self) -> ReactionMotion:
        if not self.kind:
            return ReactionMotion()
        elapsed = time.monotonic() - self.started_at
        if elapsed >= self.duration:
            self.kind = ""
            return ReactionMotion()
        progress = elapsed / self.duration
        envelope = (1.0 - progress) ** 2
        wave = math.sin(progress * math.pi)
        offset_x = 0.0
        offset_y = self.strength * wave * envelope
        angle = self.angle_strength * math.sin(progress * math.pi * 3.0) * envelope
        scale_x = 1.0 + self.squash * wave * envelope
        scale_y = 1.0 - self.squash * 0.75 * wave * envelope
        shake_x = 0.0
        if self.kind in {"rapid", "drag"}:
            shake_x = math.sin(progress * math.pi * 8.0) * self.strength * envelope
        return ReactionMotion(
            offset_x=offset_x,
            offset_y=offset_y,
            angle=angle,
            scale_x=scale_x,
            scale_y=scale_y,
            shake_x=shake_x,
        )
