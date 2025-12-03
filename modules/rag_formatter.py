# path: modules/rag_formatter.py
# version: v0.1
# purpose: Utility helpers for formatting and summarizing RAG search hits

from __future__ import annotations

import datetime
from typing import Dict, List, Optional


def format_hit(hit, score_hint: Optional[float] = None) -> Dict[str, str | float]:
    payload = getattr(hit, "payload", {}) or {}
    text = (
        payload.get("answer")
        or payload.get("result")
        or payload.get("text")
        or payload.get("user_input")
        or ""
    )
    created_at = payload.get("created_at") or payload.get("timestamp") or datetime.datetime.now().isoformat()
    source = payload.get("source") or payload.get("module") or payload.get("source_name") or "unknown"
    score = score_hint if score_hint is not None else payload.get("rating") or payload.get("score") or 0.0
    return {
        "id": str(getattr(hit, "id", payload.get("id", ""))),
        "text": text,
        "score": float(score),
        "source": source,
        "created_at": created_at,
    }


def parse_datetime(value: str) -> datetime.datetime:
    try:
        return datetime.datetime.fromisoformat(value)
    except Exception:
        try:
            return datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
        except Exception:
            return datetime.datetime.min


def build_score_summary(scores: List[float]) -> Dict[str, Optional[float]]:
    cleaned = [score for score in scores if isinstance(score, (int, float))]
    if not cleaned:
        return {"min": None, "max": None, "avg": None, "p95": None}
    cleaned.sort()
    avg = sum(cleaned) / len(cleaned)
    p95_index = min(max(int(len(cleaned) * 0.95) - 1, 0), len(cleaned) - 1)
    return {
        "min": cleaned[0],
        "max": cleaned[-1],
        "avg": avg,
        "p95": cleaned[p95_index],
    }


def apply_sort(entries: List[Dict[str, str | float]], order_by: str, descending: bool) -> List[Dict[str, str | float]]:
    reverse = descending
    key_fn = (
        (lambda entry: entry["score"]) if order_by == "score" else (lambda entry: parse_datetime(str(entry["created_at"])))
    )
    entries.sort(key=key_fn, reverse=reverse)
    return entries


def collect_source_counts(entries: List[Dict[str, str | float]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for entry in entries:
        source = str(entry.get("source", "unknown"))
        counts[source] = counts.get(source, 0) + 1
    return counts


def build_context_text(items: List[Dict[str, str | float]]) -> str:
    if not items:
        return "情報不足"
    segments: List[str] = []
    for idx, item in enumerate(items, start=1):
        text = item.get("text") or item.get("answer") or item.get("result") or ""
        source = item.get("source") or item.get("module") or "unknown"
        segments.append(f"[{idx}] ({source})\n{text}")
    return "\n---\n".join(segments)
