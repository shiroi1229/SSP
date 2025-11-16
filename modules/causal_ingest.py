"Ingest causal events from operational logs."

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Dict, List

from modules.causal_graph import causal_graph, CausalEvent

HISTORY_PATH = Path("logs/context_history.json")


def ingest_from_history(limit: int = 200) -> Dict[str, object]:
    if not HISTORY_PATH.exists():
        return {"success": False, "detail": "logs/context_history.json not found."}

    entries = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        return {"success": False, "detail": "Context history malformed."}

    selected = entries[-limit:]
    last_by_layer: Dict[str, str] = {}
    created: List[str] = []

    for idx, entry in enumerate(selected):
        timestamp = entry.get("timestamp") or entry.get("created_at") or ""
        key = entry.get("key") or entry.get("layer") or "unknown"
        layer = entry.get("layer") or "unknown"
        event_id = f"{layer}-{key}-{idx}-{uuid.uuid4().hex[:6]}"
        parents = []
        if layer in last_by_layer:
            parents.append(last_by_layer[layer])
        if created:
            parents.append(created[-1])
        new_value = entry.get("new_value") or {}
        emotion_contribution = new_value.get("detailed_emotion_state") or new_value.get("emotion_state") or {}
        knowledge_sources = []
        if isinstance(new_value, dict):
            context = new_value.get("snapshot") or new_value
            if isinstance(context, dict) and "context" in context:
                knowledge_sources.append(context["context"].get("key", "context"))
        confidence = float(new_value.get("harmony") or new_value.get("focus") or 0.0)
        context_features = {k: v for k, v in new_value.items() if isinstance(v, (int, float))}
        event = CausalEvent(
            event_id=event_id,
            type=layer,
            timestamp=timestamp,
            description=f"{key} update",
            parents=parents,
            emotion_contribution=emotion_contribution,
            knowledge_sources=knowledge_sources,
            context_features=context_features,
            confidence=confidence,
            metadata={
                "reason": entry.get("reason"),
                "old_value": entry.get("old_value"),
                "new_value": entry.get("new_value"),
            },
        )
        causal_graph.add_event(event)
        last_by_layer[layer] = event_id
        created.append(event_id)

    return {"success": True, "created": created, "count": len(created)}
