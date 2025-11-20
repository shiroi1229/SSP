from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from modules.log_manager import log_manager

POC_LOG = Path("logs/r_v0_3_poc.jsonl")
POC_SUMMARY = Path("logs/r_v0_3_poc_summary.json")


def load_summary() -> dict:
    if not POC_SUMMARY.exists():
        return {}
    try:
        import json

        return json.loads(POC_SUMMARY.read_text(encoding="utf-8"))
    except Exception:
        return {}


def check_recent_run() -> None:
    now = datetime.utcnow()
    summary = load_summary()
    last_run_str = summary.get("last_run")
    if not last_run_str:
        log_manager.warning("[R-v0.3.1] PoC summary missing last_run timestamp.")
        return
    try:
        last_run = datetime.fromisoformat(last_run_str)
    except ValueError:
        log_manager.warning("[R-v0.3.1] Invalid last_run format: %s", last_run_str)
        return
    if now - last_run > timedelta(hours=24):
        log_manager.warning("[R-v0.3.1] PoC has not run in the last 24h (last: %s).", last_run_str)
    else:
        delta = now - last_run
        log_manager.info(f"[R-v0.3.1] PoC last run was {delta} ago.")


def count_log_entries() -> int:
    if not POC_LOG.exists():
        return 0
    return sum(1 for _ in POC_LOG.open("r", encoding="utf-8"))


def main() -> None:
    total = count_log_entries()
    log_manager.info(f"[R-v0.3.1] PoC log entries: {total}")
    if total == 0:
        log_manager.warning("[R-v0.3.1] No PoC log entries found.")
    check_recent_run()


if __name__ == "__main__":
    main()
