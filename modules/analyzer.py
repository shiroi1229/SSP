"""Awareness analyzer that derives metrics from observed signals."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

SCHEMA_PATH = Path(__file__).resolve().parent / "schema" / "metrics.yaml"


class AwarenessAnalyzer:
    """Analyzes observation payloads and maps them to awareness metrics."""

    def __init__(self, schema_path: Path | str | None = None) -> None:
        self.schema_path = Path(schema_path) if schema_path else SCHEMA_PATH
        self.definition = self._load_schema()
        self._strategies = {
            "self_coherence": self._score_self_coherence,
            "cognitive_drift": self._score_cognitive_drift,
            "emotional_stability": self._score_emotional_stability,
        }

    def _load_schema(self) -> Dict[str, Any]:
        if not self.schema_path.exists():
            return {"metrics": []}
        try:
            with self.schema_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError:
            return {"metrics": []}

    def analyze(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        snapshot = observation.get("snapshot", {})
        backend_state = snapshot.get("backend_state", {})
        frontend_introspection = snapshot.get("frontend_state", {}).get("introspection", {})
        context_sources = snapshot.get("context_vector", {}).get("sources", {})

        results: Dict[str, Any] = {}
        for metric_def in self.definition.get("metrics", []):
            key = metric_def.get("key")
            strategy = self._strategies.get(key)
            if not key or not strategy:
                continue
            score = strategy(backend_state, frontend_introspection, context_sources)
            results[key] = {
                "name": metric_def.get("name", key),
                "description": metric_def.get("description", ""),
                "score": round(score, 3),
                "goal": metric_def.get("goal", "HIGH"),
            }
        return results

    def _score_self_coherence(
        self,
        backend_state: Dict[str, Any],
        *_: Any,
    ) -> float:
        positives = backend_state.get("positives", 0)
        total = backend_state.get("count") or positives
        total = total if total > 0 else positives
        total = total + backend_state.get("negatives", 0)
        if total <= 0:
            return 0.5
        return min(1.0, (positives + 1) / (total + 1))

    def _score_cognitive_drift(
        self,
        backend_state: Dict[str, Any],
        __: Dict[str, Any],
        context_sources: Dict[str, Any],
    ) -> float:
        negatives = backend_state.get("negatives", 0)
        total = backend_state.get("count", 0)
        total = total if total > 0 else negatives + 1
        context_cycles = context_sources.get("introspection_entries", 0)
        reactor = negatives + context_cycles * 0.1
        return round(min(1.0, reactor / total), 3)

    def _score_emotional_stability(
        self,
        _: Dict[str, Any],
        introspection: Dict[str, Any],
        __: Dict[str, Any],
    ) -> float:
        valence = introspection.get("avg_valence")
        if valence is None:
            return 0.6
        normalized = min(5, max(-5, valence))
        return round(max(0.0, 1 - (abs(normalized) / 5)), 3)
