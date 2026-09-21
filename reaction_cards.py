from __future__ import annotations

import random


ACTION_CARD_FILES = {
    "idle": ("collection2_03", "collection3_02", "collection3_08"),
    "welcome": ("collection2_01", "collection3_01", "collection3_09"),
    "study": ("collection3_08", "collection2_03"),
    "eat": ("collection2_02", "collection2_08", "collection3_03"),
    "drink": ("collection2_01", "collection3_02"),
    "daydream": ("collection2_03", "collection2_07", "collection3_08"),
    "cheer": ("collection2_01", "collection2_06", "collection3_01"),
    "sleep": ("collection2_05", "collection3_06"),
    "stretch": ("collection2_06", "collection3_01"),
    "shy": ("collection3_04", "collection3_08"),
    "look_fireworks": ("collection2_04", "collection3_05", "collection3_07"),
}


def choose_card_name(action: str) -> str | None:
    choices = ACTION_CARD_FILES.get(action)
    if not choices:
        return None
    return random.choice(choices)
