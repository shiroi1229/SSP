from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

router = APIRouter()

PREDICTIVE_LOG = Path("logs/predictive_self_correction.json")
SELF_HEALING_LOG = Path("logs/self_healing_daemon.log")


def _load_predictive_alerts(limit: int = 20) -> List[Dict[str, Any]]:
    if not PREDICTIVE_LOG.exists():
        return []
    try:
        data = json.loads(PREDICTIVE_LOG.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return []
    except json.JSONDecodeError:
        return []

    alerts: List[Dict[str, Any]] = []
    for entry in data[-limit:]:
        if not isinstance(entry, dict):
            continue
        prob = float(entry.get("pred_prob") or entry.get("predicted_probability") or 0)
        severity = "high" if prob >= 0.7 else "medium" if prob >= 0.4 else "low"
        alerts.append(
            {
                "timestamp": entry.get("timestamp"),
                "probability": prob,
                "action": entry.get("action"),
                "context": entry.get("context_id"),
                "severity": severity,
            }
        )
    return list(reversed(alerts))


def _load_self_healing_events(limit: int = 20) -> List[Dict[str, Any]]:
    if not SELF_HEALING_LOG.exists():
        return []
    lines = SELF_HEALING_LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    events: List[Dict[str, Any]] = []
    for line in lines[-500:]:
        level = "info"
        if "ERROR" in line:
            level = "error"
        elif "WARN" in line or "WARNING" in line:
            level = "warn"
        events.append({"line": line[-200:], "level": level})
    return events[-limit:]


RULES = [
    {
        "id": "CF-001",
        "name": "High Risk Predictive Alert",
        "description": "pred_prob >= 0.7 triggers immediate review",
        "status": "active",
    },
    {
        "id": "CF-002",
        "name": "Self-Healing Failure",
        "description": "self_healing_daemon log contains ERROR",
        "status": "active",
    },
    {
        "id": "CF-003",
        "name": "Latency Spike Watch",
        "description": "predictive log latency field exceeds threshold",
        "status": "monitoring",
    },
]


@router.get("/robustness/firewall")
def get_cognitive_firewall_state():
    predictive_alerts = _load_predictive_alerts()
    healing_events = _load_self_healing_events()

    summary = {
        "highRiskAlerts": sum(1 for alert in predictive_alerts if alert["severity"] == "high"),
        "mediumRiskAlerts": sum(1 for alert in predictive_alerts if alert["severity"] == "medium"),
        "selfHealingWarnings": sum(1 for event in healing_events if event["level"] != "info"),
    }

    return {
        "rules": RULES,
        "predictiveAlerts": predictive_alerts,
        "selfHealingEvents": healing_events,
        "summary": summary,
    }
