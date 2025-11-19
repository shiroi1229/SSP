"""Cluster health endpoints for R-v0.5."""

from __future__ import annotations

from fastapi import APIRouter

from backend.cluster.health_checker import health_checker

router = APIRouter(tags=["Cluster"], prefix="/api/cluster")


@router.get("/health")
def get_cluster_health():
    metrics = health_checker.collect()
    anomalies = health_checker.detect_anomalies()
    return {"metrics": metrics, "anomalies": anomalies}
