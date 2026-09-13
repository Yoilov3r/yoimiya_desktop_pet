from __future__ import annotations

import time


class ReminderManager:
    def __init__(
        self,
        water_minutes: int = 45,
        enabled: bool = False,
    ) -> None:
        self.water_minutes = max(15, int(water_minutes))
        self.enabled = enabled
        self.started_at = time.monotonic()
        self.last_water_at = self.started_at

    def reset(self) -> None:
        self.started_at = time.monotonic()
        self.last_water_at = self.started_at

    def check(self) -> str | None:
        if not self.enabled:
            return None
        now = time.monotonic()
        if now - self.last_water_at >= self.water_minutes * 60:
            self.last_water_at = now
            return "忙了一会儿了，喝口水再继续吧。"
        return None

    def to_dict(self) -> dict[str, int | bool]:
        return {
            "enabled": self.enabled,
            "water_minutes": self.water_minutes,
        }
