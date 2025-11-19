"""Emotion Engine: text analysis to emotion vectors for TTS/OSC pipelines."""

from __future__ import annotations

import re
from typing import Any, Dict, List


class EmotionEngine:
    """Simple rule-based analyzer that outputs 5-dimensional emotion vectors."""

    AXES = ["happiness", "sadness", "anger", "fear", "calm"]

    KEYWORD_MAP: Dict[str, List[str]] = {
        "happiness": ["happy", "嬉", "楽しい", "joy", "smile", "笑"],
        "sadness": ["sad", "泣", "辛い", "悲しい", "lonely", "涙"],
        "anger": ["怒", "angry", "frustrated", "イライラ", "憤"],
        "fear": ["怖", "fear", "不安", "anxious", "anxiety", "震"],
        "calm": ["落ち着", "calm", "relax", "穏やか", "静か"],
    }

    def __init__(self) -> None:
        self._compiled_keywords: Dict[str, List[re.Pattern[str]]] = {
            axis: [re.compile(keyword, re.IGNORECASE) for keyword in keywords]
            for axis, keywords in self.KEYWORD_MAP.items()
        }

    def analyze_emotion(self, text: str, hint: str | None = None) -> Dict[str, Any]:
        """
        Produce normalized vector + dominant tag for downstream modules.

        Args:
            text: Source utterance.
            hint: Optional script/emotion cue (joy, calm etc.).
        """
        scores = {axis: 0.0 for axis in self.AXES}
        processed = text or ""

        for axis, regexes in self._compiled_keywords.items():
            score = 0.0
            for regex in regexes:
                matches = regex.findall(processed)
                score += 0.2 * len(matches)
            scores[axis] = score

        if hint:
            axis = self._map_hint_to_axis(hint)
            scores[axis] = max(scores[axis], 1.0)

        if not any(scores.values()):
            scores["calm"] = 1.0

        total = sum(scores.values())
        normalized = {axis: round(value / total, 4) for axis, value in scores.items()}

        dominant_axis = max(normalized, key=normalized.get)
        intensity = round(normalized[dominant_axis], 3)
        tags = [dominant_axis.capitalize()]

        return {
            "emotion_vector": normalized,
            "dominant_emotion": dominant_axis,
            "intensity": intensity,
            "emotion_tags": tags,
        }

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Backwards-compatible shorthand returning tags/intensity for TTS API.
        """
        analysis = self.analyze_emotion(text)
        return {
            "emotion_tags": analysis["emotion_tags"],
            "intensity": analysis["intensity"],
            "emotion_vector": analysis["emotion_vector"],
            "dominant_emotion": analysis["dominant_emotion"],
        }

    def _map_hint_to_axis(self, hint: str) -> str:
        normalized = (hint or "").strip().lower()
        mapping = {
            "joy": "happiness",
            "happy": "happiness",
            "sad": "sadness",
            "sadness": "sadness",
            "anger": "anger",
            "angry": "anger",
            "fear": "fear",
            "calm": "calm",
            "neutral": "calm",
        }
        return mapping.get(normalized, "calm")
