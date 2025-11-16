"Trace causal paths through the causal graph."

from __future__ import annotations

from typing import Dict, List

from modules.causal_graph import causal_graph, CausalEvent


def trace_event(event_id: str, depth: int = 3) -> Dict[str, object]:
    visited: List[CausalEvent] = []
    stack: List[tuple[str, int]] = [(event_id, 0)]
    seen = set()

    while stack:
        current_id, level = stack.pop()
        if current_id in seen or level > depth:
            continue
        seen.add(current_id)
        event = causal_graph.get_event(current_id)
        if not event:
            continue
        visited.append(event)
        for parent in event.parents:
            stack.append((parent, level + 1))

    return {
        "root": event_id,
        "visited": [event.event_id for event in visited],
        "nodes": [event.__dict__ for event in visited],
    }
