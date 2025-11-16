"""Awareness observer for Cognitive Mirror (A-v3.0).

Collects lightweight signals from existing logs and persists them as
awareness snapshots for the dashboard and roadmap tracking.
"""

from __future__ import annotations

import json
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

from backend.db.connection import SessionLocal, ensure_awareness_snapshot_table
from backend.db.models import AwarenessSnapshot
from modules.log_manager import log_manager

LOGS_BASE = Path("logs")
FEEDBACK_LOG = LOGS_BASE / "feedback_loop.log"
INTROSPECTION_LOG = LOGS_BASE / "introspection_trace.log"
CONTEXT_LOG = LOGS_BASE / "context_history.json"


def _tail_lines(path: Path, limit: int = 80) -> List[str]:
    if not path.exists():
        return []
    dq: Deque[str] = deque(maxlen=limit)
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped:
                    dq.append(stripped)
    except Exception as exc:
        log_manager.warning(f"[AwarenessObserver] Failed to read {path}: {exc}")
    return list(dq)


def _parse_json_lines(lines: List[str]) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for line in lines:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def _summarize_feedback(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {"count": len(entries), "last": None, "positives": 0, "negatives": 0}
    if not entries:
        return summary
    summary["last"] = entries[-1]
    for entry in entries:
        sentiment = entry.get("sentiment") or entry.get("evaluation", {}).get("sentiment")
        if isinstance(sentiment, str):
            lowered = sentiment.lower()
            if "positive" in lowered or "good" in lowered:
                summary["positives"] += 1
            elif "negative" in lowered or "bad" in lowered:
                summary["negatives"] += 1
    return summary


def _summarize_introspection(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "count": len(entries),
        "avg_valence": None,
        "avg_arousal": None,
        "last": entries[-1] if entries else None,
    }
    if not entries:
        return summary

    valences: List[float] = []
    arousals: List[float] = []
    for entry in entries:
        emotion = entry.get("emotion") or {}
        val = emotion.get("valence")
        aro = emotion.get("arousal")
        if isinstance(val, (int, float)):
            valences.append(float(val))
        if isinstance(aro, (int, float)):
            arousals.append(float(aro))

    summary["avg_valence"] = round(sum(valences) / len(valences), 2) if valences else None
    summary["avg_arousal"] = round(sum(arousals) / len(arousals), 2) if arousals else None
    return summary


def _load_latest_context() -> Optional[Dict[str, Any]]:
    if not CONTEXT_LOG.exists():
        return None
    try:
        payload = json.loads(CONTEXT_LOG.read_text(encoding="utf-8"))
        if isinstance(payload, list) and payload:
            return payload[-1]
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        log_manager.warning("[AwarenessObserver] Failed to parse context_history.json")
    return None


def build_snapshot_payload() -> Dict[str, Any]:
    feedback_entries = _parse_json_lines(_tail_lines(FEEDBACK_LOG))
    introspection_entries = _parse_json_lines(_tail_lines(INTROSPECTION_LOG))
    latest_context = _load_latest_context()

    backend_state = _summarize_feedback(feedback_entries)
    frontend_state = {
        "introspection": _summarize_introspection(introspection_entries),
        "context": latest_context,
    }
    robustness_state = {
        "log_sources": {
            "feedback_loop": FEEDBACK_LOG.exists(),
            "introspection_trace": INTROSPECTION_LOG.exists(),
            "context_history": CONTEXT_LOG.exists(),
        },
        "last_updated": datetime.utcnow().isoformat(),
    }

    summary_lines: List[str] = []
    if backend_state["last"]:
        summary_lines.append("Backend更新: {}".format(backend_state["last"].get("summary", "(details)")))
    introspection = frontend_state["introspection"]
    if introspection.get("avg_valence") is not None:
        summary_lines.append(
            f"感情 val={introspection['avg_valence']} / arousal={introspection.get('avg_arousal')}"
        )
    if latest_context:
        summary_lines.append(f"Contextタグ: {latest_context.get('tag', 'N/A')}")

    awareness_summary = " | ".join(summary_lines) if summary_lines else "ログ情報が不足しています"
    context_vector = {
        "timestamp": datetime.utcnow().isoformat(),
        "sources": {
            "feedback_entries": backend_state["count"],
            "introspection_entries": introspection["count"],
        },
    }

    return {
        "backend_state": backend_state,
        "frontend_state": frontend_state,
        "robustness_state": robustness_state,
        "awareness_summary": awareness_summary,
        "context_vector": context_vector,
    }


def collect_awareness_snapshot() -> Dict[str, Any]:
    """Collects and persists a snapshot, returning the payload for logging."""
    ensure_awareness_snapshot_table()
    payload = build_snapshot_payload()
    session = SessionLocal()
    try:
        snapshot = AwarenessSnapshot(**payload)
        session.add(snapshot)
        session.commit()
        payload["id"] = snapshot.id
        log_manager.info("[AwarenessObserver] Stored awareness snapshot.")
    except Exception as exc:
        session.rollback()
        log_manager.error(f"[AwarenessObserver] Failed to store snapshot: {exc}", exc_info=True)
        raise
    finally:
        session.close()
    return payload
