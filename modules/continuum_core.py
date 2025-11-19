"""Continuum core orchestrates awareness streams for R-v2.0."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from modules.memory_store import MemoryStore
from modules.temporal_emotion import generate_emotion_signature


class ContinuumCore:
    def __init__(self) -> None:
        self.memory = MemoryStore()

    def current_state(self) -> Dict[str, object]:
        now = datetime.utcnow().isoformat()
        sessions = self.memory.latest_sessions(limit=10)
        signature = generate_emotion_signature(sessions)
        return {
            "timestamp": now,
            "continuity": {
                "past_sessions": len(sessions),
                "emotion_signature": signature,
            },
            "stream_time": now,
        }

    def stream_state(self) -> List[Dict[str, object]]:
        results: List[Dict[str, object]] = []
        for session in self.memory.latest_sessions(limit=30):
            results.append(
                {
                    "session_id": session.id,
                    "timestamp": session.created_at.isoformat() if session.created_at else None,
                    "memory_snapshot": session.context_snapshot,
                    "emotion_vector": session.emotion_vector,
                }
            )
        return results
