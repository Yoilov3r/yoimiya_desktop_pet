from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class IdleCue:
    kind: str
    progress: float
    bob_offset: float
    sway_offset: float
    rotation: float
    scale: float
    effect: str | None = None


class AnimationDirector:
    def __init__(self) -> None:
        self.started_at = time.monotonic()
        self.cue_kind = "breathe"
        self.cue_duration = 2.4
        self.next_cue_at = self.started_at + random.uniform(2.2, 4.5)
        self.effect_emitted = True

    def _choose_cue(self, mood: float, energy: float, affection: float, period: str) -> tuple[str, float]:
        choices = ["breathe", "glance", "sway", "happy"]
        weights = [2.0, 2.2, 1.8, 1.0 + affection]
        if energy < 0.35 or period == "night":
            choices.extend(("sleepy", "stretch"))
            weights.extend((2.0, 1.2))
        if mood > 0.72:
            choices.append("sparkle")
            weights.append(1.8)
        return random.choices(choices, weights=weights, k=1)[0], random.uniform(0.9, 2.0)

    def update(
        self,
        mood: float,
        energy: float,
        affection: float,
        period: str,
    ) -> tuple[IdleCue, str | None]:
        now = time.monotonic()
        if now >= self.next_cue_at:
            self.cue_kind, self.cue_duration = self._choose_cue(
                mood,
                energy,
                affection,
                period,
            )
            self.started_at = now
            self.next_cue_at = now + self.cue_duration + random.uniform(1.4, 4.2)
            self.effect_emitted = False

        progress = min(1.0, max(0.0, (now - self.started_at) / self.cue_duration))
        envelope = math.sin(progress * math.pi)
        bob_offset = 0.0
        sway_offset = 0.0
        rotation = 0.0
        scale = 1.0
        effect = None

        if self.cue_kind == "glance":
            sway_offset = math.sin(progress * math.tau) * 4.5
            rotation = math.sin(progress * math.tau) * 1.8
        elif self.cue_kind == "sway":
            sway_offset = math.sin(progress * math.tau * 1.6) * 3.2
            rotation = math.sin(progress * math.tau * 1.6) * 1.1
        elif self.cue_kind == "happy":
            bob_offset = -envelope * 5.0
            scale = 1.0 + envelope * 0.015
            effect = "hearts"
        elif self.cue_kind == "sleepy":
            bob_offset = envelope * 3.0
            rotation = math.sin(progress * math.tau) * 0.7
            effect = "zzz"
        elif self.cue_kind == "stretch":
            scale = 1.0 + envelope * 0.035
            bob_offset = -envelope * 3.0
            effect = "stars"
        elif self.cue_kind == "sparkle":
            effect = "sparkles"

        emitted = None
        if effect and not self.effect_emitted:
            emitted = effect
            self.effect_emitted = True
        return (
            IdleCue(
                kind=self.cue_kind,
                progress=progress,
                bob_offset=bob_offset,
                sway_offset=sway_offset,
                rotation=rotation,
                scale=scale,
                effect=effect,
            ),
            emitted,
        )
