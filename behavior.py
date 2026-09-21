from __future__ import annotations

import json
import random
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Sequence


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


@dataclass
class PetNeeds:
    energy: float = 0.82
    mood: float = 0.78
    fullness: float = 0.72
    focus: float = 0.66
    knowledge: float = 0.25
    affection: float = 0.12
    experience: float = 0.0
    cleanliness: float = 0.94
    health: float = 0.90
    coins: int = 0
    treats: int = 5
    drinks: int = 5

    @classmethod
    def from_dict(cls, data: Mapping[str, object] | None) -> "PetNeeds":
        if not data:
            return cls()
        values: dict[str, float] = {}
        for field in (
            "energy",
            "mood",
            "fullness",
            "focus",
            "knowledge",
            "affection",
            "experience",
            "cleanliness",
            "health",
        ):
            raw = data.get(field, getattr(cls(), field))
            try:
                values[field] = clamp(float(raw))
            except (TypeError, ValueError):
                values[field] = getattr(cls(), field)
        for field in ("coins", "treats", "drinks"):
            raw = data.get(field, getattr(cls(), field))
            try:
                values[field] = max(0, int(raw))
            except (TypeError, ValueError):
                values[field] = getattr(cls(), field)
        return cls(**values)

    def to_dict(self) -> dict[str, float]:
        return asdict(self)

    def update(self, seconds: float, action_key: str, period: str) -> None:
        seconds = max(0.0, min(seconds, 5.0))
        self.energy -= seconds * 0.00035
        self.fullness -= seconds * 0.00020
        self.focus -= seconds * 0.00012
        self.cleanliness -= seconds * 0.00008

        if action_key == "study":
            self.focus += seconds * 0.0018
            self.energy -= seconds * 0.00055
        elif action_key == "eat":
            self.fullness += seconds * 0.0042
            self.mood += seconds * 0.0006
        elif action_key == "sleep":
            self.energy += seconds * 0.0032
        elif action_key in {"cheer", "welcome"}:
            self.mood += seconds * 0.0008
        elif action_key == "daydream":
            self.mood += seconds * 0.00035
            self.focus -= seconds * 0.00020

        if period == "night" and action_key != "sleep":
            self.energy -= seconds * 0.00035

        if self.fullness < 0.18:
            self.health -= seconds * 0.00035
        elif self.fullness > 0.55 and self.energy > 0.35:
            self.health += seconds * 0.00008
        if self.cleanliness < 0.20:
            self.mood -= seconds * 0.00025

        self.energy = clamp(self.energy)
        self.mood = clamp(self.mood)
        self.fullness = clamp(self.fullness)
        self.focus = clamp(self.focus)
        self.affection = clamp(self.affection)
        self.cleanliness = clamp(self.cleanliness)
        self.health = clamp(self.health)

    @property
    def level(self) -> int:
        return 1 + int(self.experience // 100)

    @property
    def level_progress(self) -> float:
        return (self.experience % 100) / 100

    def register_interaction(self, region: str) -> None:
        affection_gain = {
            "face": 0.026,
            "hair": 0.015,
            "hand": 0.020,
            "accessory": 0.018,
            "outfit": 0.014,
        }.get(region, 0.012)
        self.affection = clamp(self.affection + affection_gain)
        self.experience += 2 + (1 if region in {"face", "hand"} else 0)
        if random.random() < 0.12:
            self.coins += 1

    def use_treat(self) -> bool:
        if self.treats <= 0:
            return False
        self.treats -= 1
        self.fullness = clamp(self.fullness + 0.38)
        self.mood = clamp(self.mood + 0.10)
        self.health = clamp(self.health + 0.04)
        self.affection = clamp(self.affection + 0.015)
        self.experience += 4
        return True

    def use_drink(self) -> bool:
        if self.drinks <= 0:
            return False
        self.drinks -= 1
        self.fullness = clamp(self.fullness + 0.08)
        self.health = clamp(self.health + 0.02)
        self.cleanliness = clamp(self.cleanliness - 0.01)
        self.experience += 2
        return True

    def apply_item_effects(self, effects: Mapping[str, float]) -> None:
        for key, value in effects.items():
            if key == "coins":
                self.coins = max(0, self.coins + int(value))
            elif hasattr(self, key):
                current = float(getattr(self, key))
                setattr(self, key, clamp(current + float(value)))

    def status_summary(self) -> str:
        return (
            f"Lv.{self.level}  好感 {self.affection:.0%}  "
            f"幸福 {self.mood:.0%}  知识 {self.knowledge:.0%}"
        )

    def important_note(self, action_key: str) -> str | None:
        if self.energy < 0.20:
            return "energy"
        if self.fullness < 0.18:
            return "hungry"
        if self.mood < 0.18:
            return "mood"
        if action_key == "study" and self.focus < 0.20:
            return "focus"
        return None

    def action_modifier(self, action_key: str, period: str) -> float:
        modifier = 1.0
        if self.energy < 0.30:
            modifier *= {"sleep": 4.8, "eat": 1.8, "study": 0.25, "cheer": 0.45}.get(action_key, 1.0)
        if self.fullness < 0.25:
            modifier *= {"eat": 4.5, "study": 0.55, "daydream": 0.75}.get(action_key, 1.0)
        if self.mood < 0.28:
            modifier *= {"welcome": 2.2, "cheer": 2.0, "eat": 1.5, "sleep": 1.3}.get(action_key, 0.8)
        if self.focus > 0.78 and action_key == "study":
            modifier *= 1.6
        if period == "night":
            modifier *= {"sleep": 3.0, "idle": 1.2, "study": 0.45, "cheer": 0.55}.get(action_key, 1.0)
        return modifier


class DialogueEngine:
    def __init__(
        self,
        defaults: Mapping[str, Sequence[str]],
        custom_path: Path,
        greeting_lines: Mapping[str, Sequence[str]] | None = None,
        builtin_path: Path | None = None,
    ) -> None:
        self.defaults = {key: list(lines) for key, lines in defaults.items()}
        self.greeting_lines = {
            key: list(lines) for key, lines in (greeting_lines or {}).items()
        }
        self.custom_path = custom_path
        self.builtin_path = builtin_path
        self.bags: dict[str, deque[str]] = {}
        self.custom: dict[str, list[str]] = {}
        self.recent: deque[str] = deque(maxlen=28)
        self.load_builtin()
        self.reload()

    @staticmethod
    def is_placeholder(line: str) -> bool:
        return "示例" in line or "自定义" in line

    def load_builtin(self) -> None:
        if self.builtin_path is None or not self.builtin_path.exists():
            return
        try:
            raw = json.loads(self.builtin_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return
        if not isinstance(raw, dict):
            return
        dialogues = raw.get("dialogues", raw)
        if not isinstance(dialogues, dict):
            return
        for key, lines in dialogues.items():
            if not isinstance(lines, list):
                continue
            clean = [str(line) for line in lines if str(line).strip() and not self.is_placeholder(str(line))]
            if not clean:
                continue
            if key in self.greeting_lines:
                self.greeting_lines[key].extend(clean)
            else:
                self.defaults.setdefault(str(key), []).extend(clean)
        greetings = raw.get("greetings")
        if isinstance(greetings, dict):
            for key, lines in greetings.items():
                if isinstance(lines, list):
                    self.greeting_lines.setdefault(str(key), []).extend(
                        str(line)
                        for line in lines
                        if str(line).strip() and not self.is_placeholder(str(line))
                    )

    def reload(self) -> None:
        if not self.custom_path.exists():
            self.write_template()
        try:
            raw = json.loads(self.custom_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            self.custom = {}
            return

        if not isinstance(raw, dict):
            self.custom = {}
            return
        self.custom = {
            str(key): [str(line) for line in value if str(line).strip()]
            for key, value in raw.items()
            if isinstance(value, list)
        }
        cleaned: dict[str, list[str]] = {}
        changed = False
        for key, lines in self.custom.items():
            clean = [line for line in lines if not self.is_placeholder(line)]
            if clean != lines:
                changed = True
            cleaned[key] = clean
        self.custom = cleaned
        if changed:
            self.custom_path.write_text(
                json.dumps(self.custom, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    def write_template(self) -> None:
        if self.custom_path.exists():
            return
        self.custom_path.parent.mkdir(parents=True, exist_ok=True)
        template = {
            "idle": [],
            "study": [],
            "eat": [],
            "daydream": [],
            "cheer": [],
            "welcome": [],
            "sleep": [],
            "head": [],
            "hair": [],
            "face": [],
            "accessory": [],
            "outfit": [],
            "body": [],
            "hand": [],
            "drag": [],
            "rapid": [],
            "stretch": [],
            "look_fireworks": [],
            "shy": [],
        }
        self.custom_path.write_text(
            json.dumps(template, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _context_candidates(
        self,
        action_key: str,
        period: str,
        needs: PetNeeds,
        extra_context: Sequence[str],
    ) -> list[str]:
        note = needs.important_note(action_key)
        context: dict[str, list[str]] = {
            "energy": [
                "眼皮有点重了……我稍微休息一下就好。",
                "精力快见底啦，先让我缓一小会儿。",
            ],
            "hungry": [
                "肚子在提醒我该吃点东西了。",
                "还有点心吗？一点点就好。",
            ],
            "mood": [
                "今天好像有点提不起精神……陪我说说话吧。",
                "唔，心情需要一点金色火花。",
            ],
            "focus": [
                "看了好久，脑袋开始打结了。",
                "先合上书，让思路透透气。",
            ],
        }
        lines: list[str] = []
        if note:
            lines.extend(context[note])
        if period == "night" and action_key not in {"sleep", "welcome"}:
            lines.append("夜深了，我会把声音放轻一点。")
        lines.extend(str(line) for line in extra_context if str(line).strip())
        return lines

    def pick(
        self,
        action_key: str,
        period: str,
        needs: PetNeeds,
        extra_context: Sequence[str] = (),
    ) -> str:
        candidates: list[str] = []
        candidates.extend(self.custom.get(action_key, []))
        candidates.extend(self.defaults.get(action_key, []))
        if not candidates:
            candidates.extend(self.custom.get("idle", []))
            candidates.extend(self.defaults.get("idle", []))

        if action_key == "welcome" and period in self.greeting_lines:
            candidates = list(self.greeting_lines[period]) + candidates

        if needs.important_note(action_key) or period == "night" or extra_context:
            candidates = self._context_candidates(
                action_key,
                period,
                needs,
                extra_context,
            ) + candidates

        return self.choose_nonrepeating(action_key, candidates)

    def choose_nonrepeating(self, bag_key: str, candidates: Sequence[str]) -> str:
        unique = list(dict.fromkeys(line for line in candidates if line.strip()))
        if not unique:
            return "……"

        bag = self.bags.get(bag_key, deque())
        bag = deque(line for line in bag if line in unique and line not in self.recent)
        while bag and bag[0] in self.recent:
            bag.popleft()
        if not bag:
            fresh = [line for line in unique if line not in self.recent]
            bag = deque(fresh or unique)
            random.shuffle(bag)
            while len(bag) > 1 and self.recent and bag[0] == self.recent[-1]:
                bag.rotate(-1)
        line = bag.popleft()
        self.bags[bag_key] = bag
        self.recent.append(line)
        return line

    def interaction_line(
        self,
        region: str,
        period: str,
        needs: PetNeeds,
        extra_context: Sequence[str] = (),
    ) -> str:
        region_defaults: dict[str, list[str]] = {
            "head": [
                "嘿嘿……头发会被你弄乱的。",
                "摸头许可，只限今天一小会儿。",
                "再摸一下，我就当成是在鼓励我啦。",
            ],
            "body": [
                "叫我有什么事吗？",
                "我一直都在认真看着桌面哦。",
                "今天也一起找点有趣的事吧。",
            ],
            "hand": [
                "击掌！今天也要顺顺利利。",
                "抓住我的手，是要一起去放烟花吗？",
                "好，给你一点小小的好运气。",
            ],
        }
        candidates = self.custom.get(region, []) + region_defaults.get(region, [])
        context = self._context_candidates(region, period, needs, extra_context)
        pool = context + candidates
        return self.choose_nonrepeating(region, pool)
