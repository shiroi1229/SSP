"Generate textual reports for causal events."

from __future__ import annotations

from typing import Dict, Any

from modules.causal_graph import causal_graph


def generate_report(event_id: str | None = None) -> Dict[str, Any]:
    graph = causal_graph.build_graph()
    nodes = graph.get("nodes", [])
    if event_id:
        node = next((item for item in nodes if item["event_id"] == event_id), None)
        if not node:
            return {"success": False, "detail": "Event not found."}
        parents = node.get("parents", [])
        metadata = node.get("metadata") or {}
        emotions = node.get("emotion_contribution") or {}
        knowledge = node.get("knowledge_sources") or []
        confidence = node.get("confidence")
        summary = (
            f"Event {event_id} ({node.get('description') or node.get('type')}) "
            f"occurred at {node.get('timestamp')} based on parents {parents or 'None'}."
        )
        summary += f" Confidence: {confidence:.2f}" if isinstance(confidence, (int, float)) else ""
        summary += f" Knowledge sources: {', '.join(knowledge) if knowledge else 'None'}."
        if emotions:
            emo_str = ", ".join(f"{k}:{v:.2f}" for k, v in emotions.items())
            summary += f" Emotion contribution: {emo_str}."
        return {
            "success": True,
            "event_id": event_id,
            "summary": summary,
            "metadata": metadata,
            "parents": parents,
        }
    else:
        summary = (
            f"Causal graph currently tracks {len(nodes)} events with "
            f"{len(graph.get('edges', []))} edges. "
            "Use /api/causal/report?event_id=<ID> for detailed context."
        )
        return {"success": True, "summary": summary, "total_nodes": len(nodes)}
