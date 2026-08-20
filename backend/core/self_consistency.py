"""Consistency analysis for thoughts, emotions, and logic."""

from __future__ import annotations

from typing import Dict


def assess_consistency(diagnostics: Dict[str, object]) -> Dict[str, object]:
    alerts = diagnostics.get("alert_count", 0)
    total_lines = diagnostics.get("line_count", 0) or 1
    findings = diagnostics.get("findings", [])
    depth_score = max(0, 100 - alerts * 12)
    coverage_score = min(100, int((len(findings) / max(1, total_lines)) * 200))
    score = max(30, min(100, depth_score + coverage_score // 2))
    return {
        "score": score,
        "alerts": alerts,
        "findings": findings,
        "summary": f"{len(findings)} consistency findings across {total_lines} log rows.",
    }
