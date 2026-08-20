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


def build_failure_plan() -> List[Dict[str, Any]]:
    """Return the ordered list of endpoints that we exercise during the PoC."""
    return [
        {
            "path": "/api/system/health",
            "method": "GET",
            "payload": None,
            "note": "Health check baseline",
        },
        {
            "path": "/api/system/metrics",
            "method": "GET",
            "payload": None,
            "note": "Collect load-balancer metrics",
        },
        {
            "path": "/api/metrics/v0_1/summary",
            "method": "GET",
            "payload": None,
            "note": "Ensure PoC metrics stay available",
        },
        {
            "path": "/api/metrics/v0_1/timeseries?hours=2",
            "method": "GET",
            "payload": None,
            "note": "Timeseries accuracy",
        },
        {
            "path": "/api/chat",
            "method": "POST",
            "payload": {"input": "", "force_error": True},
            "note": "Trigger Chat API validation with invalid payload",
        },
    ]


def inject_failures(
    session: requests.Session,
    base_url: str,
    plan: Iterable[Dict[str, Any]],
    pause: float = 1.0,
) -> List[Dict[str, Any]]:
    """Execute the failure plan against the given base URL."""
    results: List[Dict[str, Any]] = []
    for entry in plan:
        path = entry["path"]
        method = entry["method"].upper()
        url = f"{base_url.rstrip('/')}{path}"
        payload = entry.get("payload")
        params = None
        if "?" in path:
            url, _, query = url.partition("?")
            params = dict(pair.split("=") for pair in query.split("&") if "=" in pair)
        start = time.monotonic()
        try:
            logging.info("Injecting failure: %s %s", method, url)
            response = session.request(
                method,
                url,
                json=payload,
                params=params,
                timeout=10,
            )
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
            "note": entry.get("note"),
            "body": body[:1024],
        }
        results.append(result)
        time.sleep(pause)
    logging.info("Finished injecting %d failure vectors.", len(results))
    return results


def summarise(results: Iterable[Dict[str, Any]]) -> None:
    total = sum(1 for _ in results)
    successes = sum(1 for r in results if r.get("status", 0) >= 200 and r.get("status", 0) < 500)
    logging.info("Summary: %d/%d requests succeeded (2xx/3xx/4xx)", successes, total)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inject and validate R-v0.1 resilience failure scenarios."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Backend base URL")
    parser.add_argument("--pause", type=float, default=1.0, help="Pause between requests")
    parser.add_argument("--iterations", type=int, default=1, help="How many times to run the plan")

    args = parser.parse_args()
    session = requests.Session()
    plan = build_failure_plan()
    all_results: List[Dict[str, Any]] = []
    for i in range(args.iterations):
        logging.info("Starting failure injection iteration %d/%d", i + 1, args.iterations)
        all_results.extend(inject_failures(session, args.base_url, plan, pause=args.pause))
    summarise(all_results)
    for result in all_results:
        logging.info(
            "  %s %s => %s (%0.2fs) %s",
            result["method"],
            result["path"],
            result["status"],
            result["duration"],
            result["note"],
        )


if __name__ == "__main__":
    main()
