"""API endpoints for R-v0.3 Diagnostic + Alert UX."""

from __future__ import annotations

from fastapi import APIRouter

from modules.alert_manager import AlertManager
from modules.diagnostic_engine import DiagnosticEngine
from modules.insight_linker import InsightLinker
from modules.log_manager import log_manager

router = APIRouter(tags=["System"], prefix="/api/system")

_diagnostic_engine = DiagnosticEngine()
_alert_manager = AlertManager()
_insight_linker = InsightLinker()


@router.get("/diagnose")
def get_diagnostic_summary() -> dict:
    """Return the latest diagnostic findings plus alert and insight context."""
    log_manager.info("[SystemDiagnose] Generating diagnostic summary.")
    findings_summary = _diagnostic_engine.analyze_recent_logs()
    findings = findings_summary.get("findings", [])
    alert_context = _alert_manager.notify(findings)
    insight_context = _insight_linker.link(findings)
    return {
        "summary": findings_summary,
        "alert": alert_context,
        "insight": insight_context,
    }
