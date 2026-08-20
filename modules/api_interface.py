"""Insight API interface that exposes awareness reports."""

from __future__ import annotations

from fastapi import APIRouter

from modules.analyzer import AwarenessAnalyzer
from modules.meta_reporter import MetaReporter
from modules.observer import AwarenessObserver

router = APIRouter(prefix="/insight", tags=["Insight"])

_observer = AwarenessObserver()
_analyzer = AwarenessAnalyzer()
_reporter = MetaReporter()


@router.get("/report")
def get_insight_report() -> dict:
    """Return the latest awareness report for dashboards."""
    observation = _observer.collect()
    metrics = _analyzer.analyze(observation)
    narrative = _reporter.summarize(metrics, observation)
    return {
        "timestamp": observation.get("timestamp"),
        "metrics": metrics,
        "summary": narrative["summary"],
        "highlights": narrative["highlights"],
        "log_counts": observation.get("log_counts"),
        "raw_snapshot": narrative.get("raw_snapshot"),
    }
