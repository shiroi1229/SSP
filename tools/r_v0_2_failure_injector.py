from __future__ import annotations

import argparse
import logging
import time
from typing import Any, Dict, Iterable, List, Optional

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


POC_SCENARIOS: Dict[str, List[Dict[str, Any]]] = {
    "single-module": [
        {
            "path": "/api/system/health",
            "method": "GET",
            "payload": None,
            "note": "Baseline health check",
        },
        {
            "path": "/api/recovery/restart",
            "method": "POST",
            "payload": {"module": "chat"},
            "note": "Trigger manual restart for chat module",
        },
        {
            "path": "/api/system/metrics",
            "method": "GET",
            "payload": None,
            "note": "Metrics endpoint after restart",
        },
    ],
    "db-redis-down": [
        {
            "path": "/api/recovery/state_resync",
            "method": "POST",
            "payload": {"force": True},
            "note": "Force state resync command",
        },
        {
            "path": "/api/system/health",
            "method": "GET",
            "payload": None,
            "note": "Health during DB/Redis down",
        },
        {
            "path": "/api/system/metrics",
            "method": "GET",
            "payload": None,
            "note": "Metrics after resync",
        },
    ],
    "multi-module": [
        {
            "path": "/api/recovery/restart",
            "method": "POST",
            "payload": {"module": "chat"},
            "note": "Restart chat module",
        },
        {
            "path": "/api/recovery/restart",
            "method": "POST",
            "payload": {"module": "metrics"},
            "note": "Restart metrics module",
        },
        {
            "path": "/api/alert/notify",
            "method": "POST",
            "payload": {"level": "critical", "message": "Test failure"},
            "note": "Force alert notification",
        },
    ],
}


def inject_sequence(
    session: requests.Session,
    base_url: str,
    steps: Iterable[Dict[str, Any]],
    pause: float = 1.0,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for step in steps:
        path = step["path"]
        url = f"{base_url.rstrip('/')}{path}"
        method = step["method"].upper()
        payload = step.get("payload")
        start = time.monotonic()
        try:
            logging.info("Executing %s %s", method, url)
            response = session.request(method, url, json=payload, timeout=10)
            status = response.status_code
            body = response.text
        except Exception as exc:  # pragma: no cover
            logging.warning("Request failed: %s %s %s", method, url, exc)
            status = 0
            body = str(exc)
        duration = time.monotonic() - start
        result = {
            "path": path,
            "method": method,
            "status": status,
            "duration": duration,
            "note": step.get("note"),
            "body": body[:1024],
        }
        results.append(result)
        time.sleep(pause)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Fault Recovery PoC injector for R-v0.2.1")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Service base URL")
    parser.add_argument("--scenario", choices=list(POC_SCENARIOS), default="single-module")
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--pause", type=float, default=1.0)

    args = parser.parse_args()
    session = requests.Session()
    for i in range(args.iterations):
        logging.info("Scenario %s iteration %d/%d", args.scenario, i + 1, args.iterations)
        steps = POC_SCENARIOS[args.scenario]
        results = inject_sequence(session, args.base_url, steps, pause=args.pause)
        for result in results:
            logging.info(
                "  %s %s => %s (%.2fs) [%s]",
                result["method"],
                result["path"],
                result["status"],
                result["duration"],
                result["note"],
            )


if __name__ == "__main__":
    main()
