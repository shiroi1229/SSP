"""System metrics API for R-v0.4."""

from __future__ import annotations

from fastapi import APIRouter

from backend.modules.load_balancer import load_balancer_service
from backend.modules.perf_monitor import perf_monitor

router = APIRouter(tags=["System"], prefix="/system")


@router.get("/metrics")
def get_system_metrics():
    """Return perf metrics and current load balancer state."""
    metrics = perf_monitor.collect()
    balance = load_balancer_service.get_state()
    return {"metrics": metrics, "balance": balance}
