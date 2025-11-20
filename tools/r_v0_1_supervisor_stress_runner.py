from __future__ import annotations

import argparse
import logging
import statistics
import time
from typing import Any, Dict, List

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def run_supervisor_stress(
    session: requests.Session,
    base_url: str,
    duration: float = 60.0,
    interval: float = 5.0,
) -> Dict[str, Any]:
    """Run a supervised stress loop that hits /api/system/health repeatedly."""
    samples: List[Dict[str, Any]] = []
    endpoint = "/api/system/health"
    url = f"{base_url.rstrip('/')}{endpoint}"
    start = time.monotonic()
    while True:
        cycle_start = time.monotonic()
        try:
            response = session.get(url, timeout=10)
            status = response.status_code
        except Exception as exc:  # pragma: no cover
            logging.warning("Health check failed: %s", exc)
            status = 0
        cycle_duration = time.monotonic() - cycle_start
        samples.append(
            {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "status": status,
                "duration": cycle_duration,
            }
        )
        if duration <= 0:
            break
        elapsed = time.monotonic() - start
        if elapsed >= duration:
            break
        time.sleep(interval)
    durations = [sample["duration"] for sample in samples if sample["duration"] >= 0]
    summary = {
        "samples": len(samples),
        "average_duration": statistics.mean(durations) if durations else 0.0,
        "status_counts": {
            str(status): sum(1 for sample in samples if sample["status"] == status)
            for status in set(sample["status"] for sample in samples)
        },
        "total_duration": time.monotonic() - start,
    }
    return {"samples": samples, "summary": summary}


def main() -> None:
    parser = argparse.ArgumentParser(description="Stress Supervisor-managed services for R-v0.1.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Backend base URL")
    parser.add_argument("--duration", type=float, default=60.0, help="Total stress duration in seconds")
    parser.add_argument("--interval", type=float, default=5.0, help="Interval between health checks")

    args = parser.parse_args()
    session = requests.Session()
    runner_output = run_supervisor_stress(session, args.base_url, args.duration, args.interval)
    summary = runner_output["summary"]
    logging.info("Supervisor stress completed: %d samples", summary["samples"])
    for status, count in summary["status_counts"].items():
        logging.info("  status %s: %d hits", status, count)
    logging.info("Average health check duration: %.3fs", summary["average_duration"])


if __name__ == "__main__":
    main()
