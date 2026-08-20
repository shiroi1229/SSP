"""Insight Linker consolidates diagnostic results with awareness metrics."""

from __future__ import annotations

from typing import Dict, List

from modules.api_interface import get_insight_report


class InsightLinker:
    """Links diagnostic findings with Insight Engine outputs."""

    def link(self, findings: List[Dict[str, object]]) -> Dict[str, object]:
        insight_report = get_insight_report()
        return {
            "insight_timestamp": insight_report.get("timestamp"),
            "metrics": insight_report.get("metrics"),
            "summary": insight_report.get("summary"),
            "insight_highlights": insight_report.get("highlights"),
            "matched_findings": len(findings),
        }
