"""
Knowledge base overview endpoint for visual dashboards.
Provides aggregated stats (totals, source distribution, timeline, score bins)
so the frontend can render an at-a-glance view of what has been ingested.
"""
from collections import Counter, defaultdict
from datetime import datetime, date
from typing import Dict, List

from fastapi import APIRouter, Query

from modules.rag_engine import RAGEngine
from modules.log_manager import log_manager

router = APIRouter()
rag = RAGEngine()


def _safe_parse_date(value: str) -> date | None:
    try:
        return datetime.fromisoformat(value).date()
    except Exception:
        return None


def _collect_embeddings(max_items: int) -> List[dict]:
    """Fetch embeddings in batches for aggregation.

    We intentionally cap the amount of data scanned to avoid expensive
    full-collection walks on large deployments.
    """
    items: List[dict] = []
    page_size = 200
    offset = 0

    while len(items) < max_items:
        remaining = max_items - len(items)
        batch_limit = min(page_size, remaining)
        batch = rag.list_embeddings(
            limit=batch_limit,
            offset=offset,
            order_by="created_at",
            descending=False,
        )
        batch_items = batch.get("items", [])
        if not batch_items:
            break
        items.extend(batch_items)
        # When scroll runs out of results it will return fewer items than requested
        if len(batch_items) < batch_limit:
            break
        offset += batch_limit
    return items


def _build_timeline(items: List[dict]) -> List[Dict[str, int]]:
    per_day: Dict[date, int] = defaultdict(int)
    for entry in items:
        parsed = _safe_parse_date(str(entry.get("created_at", "")))
        if parsed:
            per_day[parsed] += 1
    return [
        {"date": day.isoformat(), "count": per_day[day]} for day in sorted(per_day)
    ]


def _build_score_bins(items: List[dict], bin_count: int = 10) -> Dict[str, list]:
    scores = [float(entry.get("score", 0.0)) for entry in items]
    if not scores:
        return {"bins": [], "counts": []}
    min_score = min(scores)
    max_score = max(scores)
    if min_score == max_score:
        return {"bins": [min_score], "counts": [len(scores)]}

    step = (max_score - min_score) / bin_count
    bins = [min_score + step * i for i in range(bin_count + 1)]
    counts = [0 for _ in range(bin_count)]

    for score in scores:
        # Clamp the last value into the final bin to handle floating precision.
        index = min(int((score - min_score) / step), bin_count - 1)
        counts[index] += 1

    return {
        "bins": [round(boundary, 3) for boundary in bins],
        "counts": counts,
    }


@router.get("/knowledge/overview")
def knowledge_overview(max_items: int = Query(500, ge=50, le=5000)):
    """Aggregate knowledge ingestion health for dashboards."""
    try:
        items = _collect_embeddings(max_items)
        total = len(items)
        source_counts = dict(Counter(entry.get("source", "unknown") for entry in items))
        timeline = _build_timeline(items)
        score_bins = _build_score_bins(items)
        sorted_items = sorted(
            items,
            key=lambda entry: str(entry.get("created_at", "")),
            reverse=True,
        )
        recent = sorted_items[:15]

        return {
            "fetched": total,
            "sources": source_counts,
            "timeline": timeline,
            "score_distribution": score_bins,
            "recent": recent,
        }
    except Exception as exc:
        log_manager.exception(f"Failed to build knowledge overview: {exc}")
        return {
            "fetched": 0,
            "sources": {},
            "timeline": [],
            "score_distribution": {"bins": [], "counts": []},
            "recent": [],
            "error": "Knowledge overview is currently unavailable.",
        }
