"""Shared logic for summarizing session analytics."""

from collections import defaultdict
from datetime import datetime
from typing import Iterable, List, Dict

from backend.db.models import SessionLog


def build_session_summary(sessions: Iterable[SessionLog]) -> Dict[str, object]:
    session_list = list(sessions)
    scores: List[float] = [
        float(s.evaluation_score)
        for s in session_list
        if isinstance(getattr(s, "evaluation_score", None), (int, float))
    ]
    avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
    buckets: Dict[str, List[float]] = defaultdict(list)
    for s in session_list:
        if isinstance(getattr(s, "evaluation_score", None), (int, float)) and getattr(s, "created_at", None):
            buckets[s.created_at.date().isoformat()].append(float(s.evaluation_score))

    series: List[Dict[str, object]] = []
    for day in sorted(buckets.keys()):
        day_scores = buckets[day]
        series.append(
            {
                "date": day,
                "avg_score": round(sum(day_scores) / len(day_scores), 3),
                "count": len(day_scores),
            }
        )

    trend_delta = 0.0
    trend_direction = "flat"
    if len(series) >= 2:
        last = series[-1]["avg_score"]
        prev = series[-2]["avg_score"]
        trend_delta = round(last - prev, 3)
        if trend_delta > 0.01:
            trend_direction = "up"
        elif trend_delta < -0.01:
            trend_direction = "down"

    return {
        "total_sessions": len(session_list),
        "average_score": avg_score,
        "series": series,
        "trend": {"delta": trend_delta, "direction": trend_direction},
    }
