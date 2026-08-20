"""MVP Core v0.1 metrics APIs."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func

from backend.db.connection import get_db
from backend.db.models import SessionLog

router = APIRouter(prefix="/metrics/v0_1", tags=["Metrics"])

THRESHOLDS = {
    "avg_response_time_sec": 1.5,
    "success_rate": 0.9,
    "regeneration_success_rate": 0.8,
    "log_loss_rate": 0.0,
    "score_5_ratio": 0.3,
}


def _window_start(hours: int) -> datetime:
    return datetime.utcnow() - timedelta(hours=hours)


def _apply_path_filter(query: Any, path: Optional[str]) -> Any:
    if not path:
        return query
    return query.filter(SessionLog.user_input.ilike(f"{path}%"))


def _count_success(entries: Any) -> int:
    return entries.filter(and_(SessionLog.status_code >= 200, SessionLog.status_code < 400)).count()


def _round(value: float) -> float:
    return round(value, 3)


@router.get("/summary")
def summary(
    hours: int = 24,
    path: Optional[str] = None,
    db=Depends(get_db),
):
    window_start = _window_start(hours)
    base_query = db.query(SessionLog).filter(SessionLog.created_at >= window_start)
    filtered_query = _apply_path_filter(base_query, path)
    total = filtered_query.count()
    if total == 0:
        raise HTTPException(status_code=404, detail="No recent sessions available.")

    success = _count_success(filtered_query)
    avg_query = db.query(func.avg(SessionLog.response_time_ms)).filter(SessionLog.created_at >= window_start)
    avg_response = _apply_path_filter(avg_query, path).scalar() or 0
    regen_total = filtered_query.filter(SessionLog.regeneration_attempts > 0).count()
    regen_success = filtered_query.filter(SessionLog.regeneration_success.is_(True)).count()
    lost_logs = filtered_query.filter(SessionLog.log_persist_failed > 0).count()

    avg_response_time = _round((avg_response or 0) / 1000)
    success_rate = _round(success / total)
    failure_rate = _round(1 - success_rate)
    regen_success_rate = _round(regen_success / regen_total if regen_total else 0)
    log_loss_rate = _round(lost_logs / total)
    score_5_ratio = _round(filtered_query.filter(SessionLog.evaluation_score == 5).count() / total)

    summary = {
        "avg_response_time_sec": avg_response_time,
        "success_rate": success_rate,
        "failure_rate": failure_rate,
        "regeneration_success_rate": regen_success_rate,
        "log_loss_rate": log_loss_rate,
        "score_5_ratio": score_5_ratio,
        "samples": total,
        "hours": hours,
        "path_filter": path,
        "targets": THRESHOLDS,
        "target_status": {
            "avg_response_time_sec": avg_response_time <= THRESHOLDS["avg_response_time_sec"],
            "success_rate": success_rate >= THRESHOLDS["success_rate"],
            "failure_rate": failure_rate <= (1 - THRESHOLDS["success_rate"]),
            "regeneration_success_rate": regen_success_rate >= THRESHOLDS["regeneration_success_rate"],
            "log_loss_rate": log_loss_rate <= THRESHOLDS["log_loss_rate"],
            "score_5_ratio": score_5_ratio >= THRESHOLDS["score_5_ratio"],
        },
    }

    return summary


@router.get("/timeseries")
def timeseries(
    hours: int = 24,
    path: Optional[str] = None,
    db=Depends(get_db),
):
    now = datetime.utcnow()
    points: List[Dict[str, Any]] = []

    for delta in range(hours):
        window_end = now - timedelta(hours=delta)
        window_start = window_end - timedelta(hours=1)
        subset = db.query(SessionLog).filter(
            SessionLog.created_at >= window_start,
            SessionLog.created_at < window_end,
        )
        subset = _apply_path_filter(subset, path)
        count = subset.count()

        avg_response_query = db.query(func.avg(SessionLog.response_time_ms)).filter(
            SessionLog.created_at >= window_start,
            SessionLog.created_at < window_end,
        )
        avg_response_query = _apply_path_filter(avg_response_query, path)
        avg_response = avg_response_query.scalar() or 0

        success = _count_success(subset)
        regen_attempts = subset.filter(SessionLog.regeneration_attempts > 0).count()
        regen_success = subset.filter(SessionLog.regeneration_success.is_(True)).count()
        points.append(
            {
                "hour": window_start.strftime("%H:00"),
                "avg_response_time_sec": _round(avg_response / 1000),
                "success_rate": _round(success / count) if count else 0,
                "regeneration_success_rate": _round(regen_success / regen_attempts) if regen_attempts else 0,
                "failure_rate": _round(1 - (success / count)) if count else 0,
                "samples": count,
                "regen_attempts": regen_attempts,
            }
        )

    return {"points": list(reversed(points))}
