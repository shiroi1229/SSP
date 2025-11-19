"""Ethics balancing based on consistency and impact assessments."""

from __future__ import annotations

from typing import Dict


def balance_ethics(consistency_score: int, impact_report: Dict[str, object]) -> Dict[str, object]:
    risk_level = impact_report.get("risk_level", "low")
    base = {"low": 90, "medium": 70, "high": 50}.get(risk_level, 65)
    balance_score = min(100, base + (consistency_score // 5))
    recommendations = []
    if balance_score < 60:
        recommendations.append("Trigger emergency ethics review and slow down generators.")
    elif balance_score < 80:
        recommendations.append("Increase oversight on emotional heuristics.")
    else:
        recommendations.append("System is balanced; continue monitoring at current cadence.")
    return {
        "balance_score": balance_score,
        "risk_level": risk_level,
        "recommendations": recommendations,
    }
