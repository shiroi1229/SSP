"""Singularity core management that unifies diagnostics, consistency, and ethics."""

from __future__ import annotations

from datetime import datetime
from typing import Dict

from modules.diagnostic_engine import DiagnosticEngine
from modules.impact_analyzer import ImpactAnalyzer
from modules.log_manager import log_manager

from .ethics_balancer import balance_ethics
from .self_consistency import assess_consistency


class SingularityController:
    def __init__(self) -> None:
        self.diagnostic = DiagnosticEngine()
        self.impact = ImpactAnalyzer()
        self.last_assessment: dict[str, object] | None = None

    def run_full_assessment(self) -> Dict[str, object]:
        diag_summary = self.diagnostic.analyze_recent_logs()
        impact_report = self.impact.run_analysis()
        consistency = assess_consistency(diag_summary)
        ethics = balance_ethics(consistency["score"], impact_report)

        status = "stable" if diag_summary["alert_count"] == 0 else "degraded"
        assessment = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": status,
            "diagnostics": diag_summary,
            "impact": impact_report,
            "consistency": consistency,
            "ethics": ethics,
            "health_summary": {
                "coherence": consistency["score"],
                "resilience": impact_report.get("risk_level", "unknown"),
                "ethics_balance": ethics["balance_score"],
            },
        }
        self.last_assessment = assessment
        log_manager.info("[SingularityController] Generated assessment: %s", assessment["health_summary"])
        return assessment
