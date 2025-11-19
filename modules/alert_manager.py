"""Alert Manager that routes diagnostic findings into notification channels."""

from __future__ import annotations

from typing import Dict, List

from modules.alert_dispatcher import AlertDispatcher
from modules.log_manager import log_manager


class AlertManager:
    """Wraps AlertDispatcher to send contextualized diagnostic alerts."""

    def __init__(self) -> None:
        self.dispatcher = AlertDispatcher()

    def notify(self, findings: List[Dict[str, object]], source: str = "DiagnosticEngine") -> Dict[str, object]:
        if not findings:
            log_manager.info("[AlertManager] No findings to dispatch.")
            return {"status": "skipped", "reason": "no_findings"}

        categories = ", ".join({finding.get("category", "unknown") for finding in findings})
        highest = max(findings, key=lambda f: f.get("confidence", 0.0))
        severity = highest.get("severity", "info")
        message = (
            f"[{source}] {len(findings)} findings ({categories}). "
            f"Top issue: {highest.get('issue')} (confidence {highest.get('confidence')})."
        )
        dispatch_result = self.dispatcher.dispatch_alert(message, severity=severity)
        return {
            "dispatched": dispatch_result,
            "primary_issue": highest.get("issue"),
            "severity": severity,
            "total_findings": len(findings),
        }
