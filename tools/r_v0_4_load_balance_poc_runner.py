from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests

POC_LOG = Path("logs/r_v0_4_poc.jsonl")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def fetch_metrics(session: requests.Session, base_url: str) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/system/metrics"
    resp = session.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()


def post_rebalance(session: requests.Session, base_url: str, modes: List[Dict[str, Any]]) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/system/rebalance"
    payload = {"modes": modes}
    resp = session.post(url, json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def run_poc(base_url: str) -> Dict[str, Any]:
    session = requests.Session()
    try:
        before = fetch_metrics(session, base_url)

        modes = [
            {"name": "normal", "cpu_max": 0.65, "mem_max": 0.7, "action": "full"},
            {"name": "degraded", "cpu_max": 0.75, "mem_max": 0.8, "action": "reduce_parallelism"},
            {"name": "throttle", "cpu_max": 0.9, "mem_max": 0.9, "action": "pause_heavy_jobs"},
        ]
        rebalance_result = post_rebalance(session, base_url, modes)

        after = fetch_metrics(session, base_url)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "base_url": base_url,
            "before": before,
            "rebalance": rebalance_result,
            "after": after,
        }
    finally:
        session.close()


def append_log(record: Dict[str, Any], log_path: Path = POC_LOG) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="R-v0.4 Adaptive Load Balancer PoC runner")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Backend base URL")
    parser.add_argument("--iterations", type=int, default=1)
    args = parser.parse_args()

    for i in range(args.iterations):
        logging.info("Running R-v0.4 load balancer PoC iteration %d/%d", i + 1, args.iterations)
        record = run_poc(args.base_url)
        record["iteration"] = i + 1
        append_log(record)
        logging.info("Recorded iteration %d with mode: %s", i + 1, record["rebalance"].get("balance", {}).get("mode", {}))


if __name__ == "__main__":
    main()

