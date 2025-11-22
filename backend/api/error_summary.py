# path: backend/api/error_summary.py
# version: v0.30
# purpose: エラーサマリAPI（Envelope出力・UTC時間窓での集計）

"""Error summary APIs for MVP Core quality tracking."""

from datetime import datetime, timedelta, UTC
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from backend.api.common import envelope_ok
from backend.api.schemas import Envelope
from sqlalchemy import func

from backend.db.connection import get_db
from backend.db.models import SessionLog

router = APIRouter(prefix="/metrics/v0_1/error_summary", tags=["Metrics"])


def _window_start(hours: int) -> datetime:
    return datetime.now(UTC) - timedelta(hours=hours)


def _apply_path_filter(query: Any, path: Optional[str]) -> Any:
    if not path:
        return query
    return query.filter(SessionLog.user_input.ilike(f"{path}%"))


@router.get("/", response_model=Envelope[dict])
def summary(
    hours: int = 24,
    path: Optional[str] = None,
    db=Depends(get_db),
):
    window_start = _window_start(hours)
    base_query = db.query(SessionLog).filter(SessionLog.created_at >= window_start)
    filtered_query = _apply_path_filter(base_query, path)
    total_sessions = filtered_query.count()
    error_query = filtered_query.filter(SessionLog.error_tag.isnot(None))
    total_errors = error_query.count()

    tag_counts = (
        error_query
        .with_entities(
            SessionLog.error_tag,
            SessionLog.impact_level,
            func.count().label("count"),
        )
        .group_by(SessionLog.error_tag, SessionLog.impact_level)
        .order_by(func.count().desc())
        .all()
    )

    impact_counts = (
        error_query
        .with_entities(SessionLog.impact_level, func.count().label("count"))
        .group_by(SessionLog.impact_level)
        .order_by(func.count().desc())
        .all()
    )

    endpoint_counts = (
        error_query
        .with_entities(SessionLog.user_input, func.count().label("count"))
        .group_by(SessionLog.user_input)
        .order_by(func.count().desc())
        .limit(5)
        .all()
    )

    failure_rate = round(total_errors / total_sessions, 3) if total_sessions else 0.0

    return envelope_ok({
        "period_hours": hours,
        "total_sessions": total_sessions,
        "total_errors": total_errors,
        "failure_rate": failure_rate,
        "errors_by_tag": [
            {"tag": tag, "impact_level": impact, "count": count}
            for tag, impact, count in tag_counts
        ],
        "impact_breakdown": [
            {"impact_level": impact, "count": count}
            for impact, count in impact_counts
        ],
        "top_error_endpoints": [
            {"endpoint": endpoint, "count": count}
            for endpoint, count in endpoint_counts
        ],
    })
