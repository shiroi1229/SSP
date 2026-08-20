from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from modules.alert_manager import AlertManager
from modules.diagnostic_engine import DiagnosticEngine
from modules.insight_linker import InsightLinker

LOG_PATH = Path("logs/feedback_loop.log")
POC_LOG = Path("logs/r_v0_3_poc.jsonl")
POC_SUMMARY = Path("logs/r_v0_3_poc_summary.json")

SCENARIOS: Dict[str, Dict[str, Any]] = {
    "baseline": {
        "description": "Baseline diagnostic summary + sanity check",
        "steps": [
            {
                "type": "inject",
                "label": "診断対象のログを追記",
                "entries": [
                    "Timeout connecting to qdrant: connection reset by peer while fetching context",
                    "ModuleNotFoundError: modules.analysis_config is missing; dependency configuration incomplete",
                    "AssertionError: invalid state detected while compiling response",
                ],
            },
            {
                "type": "diagnose",
                "label": "診断 API へリクエスト",
            },
        ],
    },
    "insight_cycle": {
        "description": "Insight レポートとの同期度をチェック",
        "steps": [
            {"type": "diagnose", "label": "Insight snapshot 1"},
            {"type": "diagnose", "label": "Insight snapshot 2"},
        ],
    },
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def append_log_entries(lines: Iterable[str]) -> int:
    entries = list(lines)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        for line in entries:
            fh.write(f"{datetime.utcnow().isoformat()} - {line}\n")
    return len(entries)


def call_diagnostic_stack(
    base_url: str,
    session: Optional[requests.Session],
    mode: str,
) -> Dict[str, Any]:
    if mode == "http" and session is not None:
        response = session.get(f"{base_url.rstrip('/')}/api/system/diagnose", timeout=10)
        response.raise_for_status()
        return response.json()

    diagnostic_engine = DiagnosticEngine()
    findings_summary = diagnostic_engine.analyze_recent_logs()
    findings = findings_summary.get("findings", [])
    alert_context = AlertManager().notify(findings)
    insight_context = InsightLinker().link(findings)
    return {"summary": findings_summary, "alert": alert_context, "insight": insight_context}


def run_scenario(
    base_url: str,
    scenario_name: str,
    session: Optional[requests.Session],
    mode: str,
    pause: float,
) -> Dict[str, Any]:
    scenario = SCENARIOS[scenario_name]
    records: List[Dict[str, Any]] = []
    total_findings = 0
    alert_attempts = 0
    for step in scenario["steps"]:
        record = {
            "scenario": scenario_name,
            "label": step["label"],
            "type": step["type"],
            "timestamp": datetime.utcnow().isoformat(),
        }
        if step["type"] == "inject":
            injected = append_log_entries(step.get("entries", []))
            record.update({"injected_logs": injected})
        elif step["type"] == "diagnose":
            start = time.monotonic()
            diagnostic_payload = call_diagnostic_stack(base_url, session, mode)
            duration_ms = int((time.monotonic() - start) * 1000)
            findings = diagnostic_payload.get("summary", {}).get("findings", [])
            record.update(
                {
                    "duration_ms": duration_ms,
                    "findings": len(findings),
                    "insight_matches": diagnostic_payload.get("insight", {}).get("matched_findings"),
                    "alert_status": diagnostic_payload.get("alert", {}).get("status"),
                    "alert_severity": diagnostic_payload.get("alert", {}).get("severity"),
                }
            )
            total_findings += len(findings)
            alert_attempts += 1
        else:
            record["note"] = "Unknown step type"
        records.append(record)
        time.sleep(pause)
    return {
        "scenario": scenario_name,
        "description": scenario["description"],
        "steps": records,
        "total_findings": total_findings,
        "alert_attempts": alert_attempts,
    }


def write_log(entry: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="R-v0.3 Diagnostic PoC runner")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Backend base URL for HTTP mode")
    parser.add_argument("--scenario", choices=list(SCENARIOS), default="baseline")
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--pause", type=float, default=1.0)
    parser.add_argument("--mode", choices=["http", "direct"], default="direct", help="Use HTTP requests or in-process modules")
    parser.add_argument("--log-path", type=Path, default=POC_LOG)

    args = parser.parse_args()
    session = requests.Session() if args.mode == "http" else None

    for iteration in range(args.iterations):
        logging.info("Running %s iteration %d/%d (mode=%s)", args.scenario, iteration + 1, args.iterations, args.mode)
        summary = run_scenario(args.base_url, args.scenario, session, args.mode, args.pause)
        summary.update(
            {
                "mode": args.mode,
                "iteration": iteration + 1,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        write_log(summary, args.log_path)
        logging.info(
            "Scenario %s completed: %d findings across %d steps, %d alert attempts",
            args.scenario,
            summary["total_findings"],
            len(summary["steps"]),
            summary["alert_attempts"],
        )

        update_summary(summary)

    if session:
        session.close()


def update_summary(latest: Dict[str, Any]) -> None:
    POC_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "last_run": latest.get("timestamp"),
        "last_iteration": latest.get("iteration"),
        "total_findings": latest.get("total_findings"),
        "alert_attempts": latest.get("alert_attempts"),
        "scenario": latest.get("scenario"),
        "insight_matches": sum(step.get("insight_matches", 0) or 0 for step in latest.get("steps", [])),
    }
    with POC_SUMMARY.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
