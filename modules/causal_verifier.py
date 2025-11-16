"Verify causal consistency for an event."

from __future__ import annotations

from typing import Dict

from modules.causal_graph import causal_graph


def verify_causality(event_id: str) -> Dict[str, object]:
    event = causal_graph.get_event(event_id)
    if not event:
        return {"success": False, "detail": "Event not found."}
    missing = [parent for parent in event.parents if not causal_graph.get_event(parent)]
    return {
        "success": len(missing) == 0,
        "event_id": event_id,
        "missing_parents": missing,
        "parent_count": len(event.parents),
    }
