from __future__ import annotations

import argparse
import logging
import statistics
import time
from typing import Dict, List

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def run_scenario(
    session: requests.Session,
    base_url: str,
    targets: List[str],
    duration: float,
    interval: float,
) -> Dict[str, Dict[str, int]]:
    states: Dict[str, List[Dict[str, float]]] = {}
    start = time.monotonic()
    while True:
        for target in targets:
            url = f"{base_url.rstrip('/')}{target}"
            try:
                response = session.get(url, timeout=10)
                status = response.status_code
            except Exception as exc:  # pragma: no cover
                logging.warning("Health call failed: %s", exc)
                status = 0
            entry = {"status": status, "duration": time.monotonic() - start}
            states.setdefault(target, []).append(entry)
        if duration <= 0:
            break
        elapsed = time.monotonic() - start
        if elapsed >= duration:
            break
        time.sleep(interval)
    summary: Dict[str, Dict[str, int]] = {}
    for target, entries in states.items():
        summary[target] = {
            "samples": len(entries),
            "avg_duration_ms": int(statistics.mean(e["duration"] for e in entries) * 1000),
            "status_counts": len([e for e in entries if e["status"] == 200]),
        }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run supervisor recovery scenarios for R-v0.2")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Backend base URL")
    parser.add_argument("--duration", type=float, default=120.0, help="Total duration in seconds")
    parser.add_argument("--interval", type=float, default=5.0, help="Interval between health checks")
    parser.add_argument(
        "--targets",
        nargs="+",
        default=["/api/system/health", "/api/recovery/state_resync"],
        help="Endpoints to poll for supervisor scenarios",
    )

    args = parser.parse_args()
    session = requests.Session()
    summary = run_scenario(session, args.base_url, args.targets, args.duration, args.interval)
    logging.info("Supervisor scenario completed")
    for target, stats in summary.items():
        logging.info(
            "  %s: %d samples, avg_duration=%dms, status200=%d",
            target,
            stats["samples"],
            stats["avg_duration_ms"],
            stats["status_counts"],
        )


if __name__ == "__main__":
    main()
