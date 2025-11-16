"""Detect bias from context history for R-v0.9."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


HISTORY_PATH = Path("logs/context_history.json")


def detect_bias(limit: int = 200, threshold: float = 0.6) -> Dict[str, object]:
    if not HISTORY_PATH.exists():
        return {"total_entries": 0, "emotion_bias": [], "knowledge_bias": [], "raw_emotions": {}, "raw_knowledge": {}}

    try:
        entries = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"total_entries": 0, "emotion_bias": [], "knowledge_bias": [], "raw_emotions": {}, "raw_knowledge": {}}

    if not isinstance(entries, list):
        return {"total_entries": 0, "emotion_bias": [], "knowledge_bias": [], "raw_emotions": {}, "raw_knowledge": {}}

    selected = entries[-limit:]
    emotion_totals: Dict[str, float] = {}
    knowledge_totals: Dict[str, float] = {}

    for entry in selected:
        new_value = entry.get("new_value") or {}
        emotion_state = new_value.get("detailed_emotion_state") or new_value.get("emotion_state") or {}
        for key, value in emotion_state.items():
            if isinstance(value, (int, float)):
                emotion_totals[key] = emotion_totals.get(key, 0.0) + float(value)

        context = new_value.get("snapshot") or new_value
        if isinstance(context, dict):
            knowledge_key = context.get("context", {}).get("key") if isinstance(context.get("context"), dict) else None
            if knowledge_key:
                knowledge_totals[knowledge_key] = knowledge_totals.get(knowledge_key, 0.0) + 1

    emotion_bias = _extract_bias(emotion_totals, threshold)
    knowledge_bias = _extract_bias(knowledge_totals, threshold, normalize=False)
    return {
        "total_entries": len(selected),
        "emotion_bias": emotion_bias,
        "knowledge_bias": knowledge_bias,
        "raw_emotions": emotion_totals,
        "raw_knowledge": knowledge_totals,
    }


def _extract_bias(totals: Dict[str, float], threshold: float, normalize: bool = True) -> List[Dict[str, float]]:
    total_sum = sum(totals.values()) or 1.0
    bias_list = []
    for key, value in totals.items():
        score = value / total_sum if normalize else value
        if score >= threshold:
            bias_list.append({"label": key, "score": round(score if normalize else (value / total_sum), 3)})
    bias_list.sort(key=lambda item: item["score"], reverse=True)
    return bias_list[:5]
