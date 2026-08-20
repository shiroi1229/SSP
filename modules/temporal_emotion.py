"""Temporal emotion utilities for R-v2.0."""

from __future__ import annotations

from typing import List, Dict, Any


def generate_emotion_signature(sessions: List[Dict[str, Any]]) -> Dict[str, float]:
    weights: Dict[str, float] = {}
    for idx, session in enumerate(sessions):
        vector = session.get("emotion_vector") or {}
        factor = 1.0 / (idx + 1)
        for key, value in vector.items():
            weights[key] = weights.get(key, 0.0) + float(value) * factor
    total = sum(abs(v) for v in weights.values()) or 1.0
    return {k: v / total for k, v in weights.items()}
