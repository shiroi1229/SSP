"""Causal graph utilities for R-v0.8."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List


GRAPH_PATH = Path("data/causal_graph.json")


@dataclass
class CausalEvent:
    event_id: str
    type: str
    timestamp: str
    description: str
    parents: List[str]
    emotion_contribution: Dict[str, float]
    knowledge_sources: List[str]
    context_features: Dict[str, float]
    confidence: float
    metadata: Dict[str, object]


class CausalGraph:
    def __init__(self, graph_path: Path = GRAPH_PATH) -> None:
        self.graph_path = graph_path
        self.events: Dict[str, CausalEvent] = {}
        self._load()

    def _load(self) -> None:
        if not self.graph_path.exists():
            self.events = {}
            return
        data = json.loads(self.graph_path.read_text(encoding="utf-8"))
        self.events = {
            eid: CausalEvent(
                event_id=eid,
                type=item.get("type", "unknown"),
                timestamp=item.get("timestamp", ""),
                description=item.get("description", ""),
                parents=item.get("parents", []),
                emotion_contribution=item.get("emotion_contribution", {}),
                knowledge_sources=item.get("knowledge_sources", []),
                context_features=item.get("context_features", {}),
                confidence=item.get("confidence", 0.0),
                metadata=item.get("metadata", {}),
            )
            for eid, item in data.items()
        }

    def _persist(self) -> None:
        payload = {eid: asdict(event) for eid, event in self.events.items()}
        self.graph_path.parent.mkdir(parents=True, exist_ok=True)
        self.graph_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_event(self, event: CausalEvent) -> None:
        self.events[event.event_id] = event
        self._persist()

    def get_event(self, event_id: str) -> CausalEvent | None:
        return self.events.get(event_id)

    def list_events(self) -> List[CausalEvent]:
        return list(self.events.values())

    def build_graph(self) -> Dict[str, object]:
        return {
            "nodes": [asdict(event) for event in self.events.values()],
            "edges": [
                {"from": parent, "to": event.event_id}
                for event in self.events.values()
                for parent in event.parents
            ],
        }


causal_graph = CausalGraph()
