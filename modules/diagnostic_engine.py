"""Diagnostic Engine for R-v0.3: categorize and explain system anomalies."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from modules.log_manager import log_manager

LOG_PATH = Path("logs/feedback_loop.log")


@dataclass
class DiagnosticFinding:
    category: str
    issue: str
    severity: str
    confidence: float
    recommendation: str
    occurrences: int
    traces: List[str]

    def to_dict(self) -> Dict[str, object]:
        return {
            "category": self.category,
            "issue": self.issue,
            "severity": self.severity,
            "confidence": self.confidence,
            "recommendation": self.recommendation,
            "occurrences": self.occurrences,
            "traces": self.traces[:3],
        }


class DiagnosticEngine:
    """Analyzes recent logs to surface meaningful causes and recovery hints."""

    CATEGORY_KEYWORDS = {
        "I/O": ["timeout", "connection reset", "broken pipe", "refused"],
        "Dependency": ["module not found", "import error", "configuration"],
        "Logic": ["assert", "value error", "type error", "invalid state"],
        "Resources": ["out of memory", "out of disk", "resource exhausted"],
    }

    SEVERITY_MAP = {
        "I/O": "high",
        "Dependency": "high",
        "Logic": "medium",
        "Resources": "critical",
    }

    def _read_recent_lines(self, limit: int = 200) -> List[str]:
        if not LOG_PATH.exists():
            log_manager.warning(f"[DiagnosticEngine] Expected log file missing: {LOG_PATH}")
            return []
        with LOG_PATH.open("r", encoding="utf-8", errors="ignore") as fh:
            lines = fh.readlines()
        return lines[-limit:]

    def _collect_matches(self, lines: List[str]) -> List[DiagnosticFinding]:
        findings: List[DiagnosticFinding] = []
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            matches = []
            for line in lines:
                low = line.lower()
                if any(keyword in low for keyword in keywords):
                    matches.append(line.strip())
            if not matches:
                continue
            severity = self.SEVERITY_MAP.get(category, "medium")
            confidence = min(0.95, 0.4 + len(matches) * 0.05)
            finding = DiagnosticFinding(
                category=category,
                issue=f"{category} anomalies detected in logs",
                severity=severity,
                confidence=round(confidence, 2),
                recommendation=f"Review the latest {category} events and verify dependencies.",
                occurrences=len(matches),
                traces=matches,
            )
            findings.append(finding)
        return findings

    def analyze_recent_logs(self, limit: int = 200) -> Dict[str, object]:
        lines = self._read_recent_lines(limit)
        findings = self._collect_matches(lines)
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "line_count": len(lines),
            "alert_count": len(findings),
            "findings": [finding.to_dict() for finding in findings],
        }
        log_manager.info(f"[DiagnosticEngine] Generated {len(findings)} findings from {LOG_PATH.name}")
        return summary
