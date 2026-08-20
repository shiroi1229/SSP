# coding: utf-8
from __future__ import annotations

from typing import Dict

EMOTION_KEYWORDS = {
    "happy": "joy",
    "joy": "joy",
    "calm": "calm",
    "sad": "sad",
    "angry": "angry",
    "mad": "angry",
    "love": "joy",
    "excite": "excited",
    "excited": "excited",
    "fear": "fear",
    "scared": "fear",
}


def parse_emotion(text: str) -> Dict[str, object]:
    lowered = text.lower()
    tags = ["Neutral"]
    intensity = 0.6
    for keyword, tag in EMOTION_KEYWORDS.items():
        if keyword in lowered:
            tags = [tag]
            intensity = 0.75 if "!" in text or "!" in lowered else 0.65
            break
    if len(text) > 140:
        intensity = min(1.0, intensity + 0.1)
    return {"emotion_tags": tags, "intensity": intensity}
