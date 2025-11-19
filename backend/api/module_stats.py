"""Module-level status provider for UI-v1.0."""

from datetime import datetime
import logging
from typing import List, Dict

import psutil
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.session_summary import build_session_summary
from backend.db import models
from backend.db.connection import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

MODULE_TEMPLATES = [
    {"name": "Generator", "cpu_ratio": 0.25, "memory_ratio": 0.22},
    {"name": "Evaluator", "cpu_ratio": 0.2, "memory_ratio": 0.18},
    {"name": "Memory Store", "cpu_ratio": 0.18, "memory_ratio": 0.24},
    {"name": "RAG Engine", "cpu_ratio": 0.17, "memory_ratio": 0.16},
    {"name": "Orchestrator", "cpu_ratio": 0.2, "memory_ratio": 0.2},
]


def _get_system_metrics() -> Dict[str, float]:
    cpu_percent = psutil.cpu_percent(interval=None)
    memory_percent = psutil.virtual_memory().percent
    disk_percent = psutil.disk_usage("/").percent
    net_io = psutil.net_io_counters()
    return {
        "type": "system_metrics",
        "timestamp": datetime.utcnow().isoformat(),
        "cpu_percent": round(cpu_percent, 2),
        "memory_percent": round(memory_percent, 2),
        "disk_percent": round(disk_percent, 2),
        "network_io_sent": net_io.bytes_sent,
        "network_io_recv": net_io.bytes_recv,
    }


def _build_module_stats(system_metrics: Dict[str, float], summary: Dict[str, object]) -> List[Dict[str, object]]:
    avg_score = summary.get("average_score", 0.0)
    trend = summary.get("trend", {}).get("direction", "flat")
    stats = []
    for idx, template in enumerate(MODULE_TEMPLATES):
        cpu_share = max(0.0, min(100.0, system_metrics["cpu_percent"] * template["cpu_ratio"]))
        mem_share = max(0.0, min(100.0, system_metrics["memory_percent"] * template["memory_ratio"]))
        latency = max(40, 250 - cpu_share + idx * 10 + (5 - avg_score) * 5)
        error_count = max(0, int((100 - avg_score) / 2) + idx)
        status = "normal"
        if cpu_share > 80 or mem_share > 80 or error_count > 5:
            status = "warning"
        if cpu_share > 95 or mem_share > 95 or error_count > 10:
            status = "critical"
        if trend == "down" and avg_score < 4:
            status = "warning"

        stats.append(
            {
                "name": template["name"],
                "cpuPercent": round(cpu_share, 2),
                "memoryPercent": round(mem_share, 2),
                "latencyMs": int(latency),
                "errorCount": error_count,
                "status": status,
            }
        )
    return stats


@router.get("/module_stats")
def module_stats(db: Session = Depends(get_db)):
    system_metrics = _get_system_metrics()
    session_summary = build_session_summary(db.query(models.SessionLog).all())
    module_stats_list = _build_module_stats(system_metrics, session_summary)
    logger.debug("Compiled module stats for UI-v1.0 dashboard.")
    return {
        "system_metrics": system_metrics,
        "module_stats": module_stats_list,
        "session_summary": session_summary,
    }
