from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


LOG_JSONL = Path("logs/v0_5_1_knowledge_poc.jsonl")
SUMMARY_JSON = Path("logs/v0_5_1_knowledge_poc_summary.json")


@dataclass
class EndpointResult:
    url: str
    status: Optional[int]
    elapsed_ms: float
    total: Optional[int] = None
    source_counts: Dict[str, int] | None = None
    error: Optional[str] = None


def percentile(values: List[float], pct: float) -> Optional[float]:
    if not values:
        return None
    sorted_values = sorted(values)
    index = min(len(sorted_values) - 1, max(int(len(sorted_values) * pct / 100) - 1, 0))
    return sorted_values[index]


def call_endpoint(session: requests.Session, url: str, params: Dict[str, Any]) -> EndpointResult:
    start = time.time()
    try:
        response = session.get(url, params=params, timeout=30)
        elapsed = (time.time() - start) * 1000
        payload: Any = None
        try:
            payload = response.json()
        except ValueError:
            payload = None
        return EndpointResult(
            url=url,
            status=response.status_code,
            elapsed_ms=elapsed,
            total=payload.get("total") if isinstance(payload, dict) else None,
            source_counts=payload.get("source_counts") if isinstance(payload, dict) else None,
        )
    except Exception as exc:
        elapsed = (time.time() - start) * 1000
        return EndpointResult(url=url, status=None, elapsed_ms=elapsed, error=str(exc))


def append_log(entry: Dict[str, Any]) -> None:
    LOG_JSONL.parent.mkdir(exist_ok=True, parents=True)
    with LOG_JSONL.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def write_summary(entries: List[Dict[str, Any]]) -> None:
    knowledge_latencies = [
        item["knowledge"]["elapsed_ms"]
        for item in entries
        if item["knowledge"]["elapsed_ms"] is not None
    ]
    search_latencies = [
        item["search"]["elapsed_ms"]
        for item in entries
        if item["search"]["elapsed_ms"] is not None
    ]
    knowledge_success = sum(1 for item in entries if item["knowledge"]["status"] == 200)
    search_success = sum(1 for item in entries if item["search"]["status"] == 200)

    aggregated = Counter()
    for item in entries:
        source_counts = item["search"].get("source_counts") or {}
        aggregated.update({k: int(v) for k, v in source_counts.items()})

    summary = {
        "last_run": datetime.utcnow().isoformat(),
        "iterations": len(entries),
        "knowledge_success_rate": round(knowledge_success / len(entries) * 100, 2)
        if entries
        else 0.0,
        "search_success_rate": round(search_success / len(entries) * 100, 2)
        if entries
        else 0.0,
        "knowledge_p95_latency_ms": percentile(knowledge_latencies, 95),
        "search_p95_latency_ms": percentile(search_latencies, 95),
        "unique_sources": len(aggregated),
        "source_counts": dict(aggregated),
        "last_query": entries[-1]["query"] if entries else None,
    }
    SUMMARY_JSON.parent.mkdir(exist_ok=True, parents=True)
    with SUMMARY_JSON.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Knowledge Viewer PoC scenario.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument(
        "--queries",
        nargs="*",
        default=[
            "Knowledge Viewer",
            "Shared Reality",
            "diagnostic loop",
            "japanese description",
            "stress test",
        ],
    )
    parser.add_argument("--order-by", choices=["created_at", "score"], default="created_at")
    parser.add_argument("--sort-direction", choices=["asc", "desc"], default="desc")

    args = parser.parse_args()
    session = requests.Session()
    executed: List[Dict[str, Any]] = []

    for idx in range(args.iterations):
        search_query = args.queries[idx % len(args.queries)]
        knowledge_url = f"{args.base_url.rstrip('/')}/api/knowledge"
        search_url = f"{args.base_url.rstrip('/')}/api/knowledge/search"

        knowledge_result = call_endpoint(
            session,
            knowledge_url,
            {
                "limit": args.limit,
                "page": 1,
                "order_by": args.order_by,
                "sort_direction": args.sort_direction,
            },
        )
        search_result = call_endpoint(
            session,
            search_url,
            {
                "q": search_query,
                "limit": args.limit,
                "page": 1,
                "order_by": "score",
                "sort_direction": "desc",
            },
        )

        iteration_record = {
            "iteration": idx + 1,
            "timestamp": datetime.utcnow().isoformat(),
            "query": search_query,
            "knowledge": knowledge_result.__dict__,
            "search": search_result.__dict__,
        }
        append_log(iteration_record)
        executed.append(iteration_record)
        print(f"[INFO] Iteration {idx + 1}: knowledge_status={knowledge_result.status}, search_status={search_result.status}")
        if idx < args.iterations - 1:
            time.sleep(args.interval)

    write_summary(executed)
    print(f"[INFO] PoC finished. Summary written to {SUMMARY_JSON}")


if __name__ == "__main__":
    main()
