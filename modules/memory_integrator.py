"""Integrate past sessions with current reasoning flows."""

from __future__ import annotations

from typing import List, Dict, Any

from modules.memory_store import MemoryStore


class MemoryIntegrator:
    def __init__(self) -> None:
        self.memory = MemoryStore()

    def continuity_chain(self, depth: int = 20) -> List[Dict[str, Any]]:
        sessions = self.memory.latest_sessions(limit=depth)
        chain: List[Dict[str, Any]] = []
        for session in sessions:
            chain.append(
                {
                    "id": session.id,
                    "topic": (session.context_snapshot or {}).get("topic"),
                    "emotion": session.emotion_vector,
                    "score": session.evaluation_score,
                    "timestamp": session.created_at.isoformat() if session.created_at else None,
                }
            )
        return chain
