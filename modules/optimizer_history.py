"""Persistent history for self-optimizer adjustments."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

HISTORY_PATH = Path("logs/meta_optimizer_history.jsonl")


def log_optimizer_result(
    optimizer_result: Dict[str, Any],
    summary: str,
    bias_report: Dict[str, Any] | None = None,
) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": optimizer_result.get("status"),
        "params": optimizer_result.get("params", {}),
        "avg_score": optimizer_result.get("avg_score"),
        "summary": summary,
        "message": optimizer_result.get("message"),
        "bias": _compact_bias(bias_report or {}),
    }
    with HISTORY_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_optimizer_history(limit: int = 50) -> List[Dict[str, Any]]:
    if not HISTORY_PATH.exists():
        return []
    entries: List[Dict[str, Any]] = []
    with HISTORY_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries[-limit:]


def _compact_bias(report: Dict[str, Any]) -> Dict[str, Any]:
    def _top(items):
        return [
            {"label": item.get("label"), "score": float(item.get("score", 0.0))}
            for item in items or []
        ][:3]

    return {
        "emotion": _top(report.get("emotion_bias")),
        "knowledge": _top(report.get("knowledge_bias")),
    }
