"""Utility script to refresh data sources used by the Quantum Safety stack."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from modules.meta_contract_system import MetaContractManager
from modules.akashic_integration import collect_akashic_state, persist_akashic_state
from modules.log_manager import log_manager

LOG_PATH = Path("logs/security_refresh.log")


def refresh_meta_contracts() -> Dict[str, Any]:
    manager = MetaContractManager()
    summary = manager.sync()
    log_manager.info(
        f"[SecurityRefresh] Meta contracts synced ({summary.get('count', 0)} entries)"
    )
    return summary


def refresh_akashic_state(persist: bool = True) -> Dict[str, Any]:
    state = collect_akashic_state()
    if persist:
        persist_akashic_state(state)
        log_manager.info("[SecurityRefresh] Akashic state persisted.")
    return state


def append_log(entry: Dict[str, Any]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry["recorded_at"] = datetime.now(timezone.utc).isoformat()
    with open(LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Refresh data sources leveraged by /api/security/verify."
    )
    parser.add_argument("--skip-meta", action="store_true", help="Do not refresh meta contracts.")
    parser.add_argument(
        "--skip-akashic", action="store_true", help="Do not collect/persist Akashic state."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Collect data without persisting Akashic snapshots or writing logs.",
    )
    args = parser.parse_args()

    summary: Dict[str, Any] = {"meta": None, "akashic": None, "errors": []}

    if not args.skip_meta:
        try:
            summary["meta"] = refresh_meta_contracts()
        except Exception as exc:  # pragma: no cover - defensive logging
            msg = f"Meta contract refresh failed: {exc}"
            log_manager.error(f"[SecurityRefresh] {msg}", exc_info=True)
            summary["errors"].append(msg)

    if not args.skip_akashic:
        try:
            state = refresh_akashic_state(persist=not args.dry_run)
            summary["akashic"] = {
                "collected_at": state.get("collected_at"),
                "has_snapshot": bool(state.get("snapshot")),
                "has_internal_dialogue": bool(state.get("internal_dialogue")),
            }
        except Exception as exc:  # pragma: no cover - defensive logging
            msg = f"Akashic refresh failed: {exc}"
            log_manager.error(f"[SecurityRefresh] {msg}", exc_info=True)
            summary["errors"].append(msg)

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if not args.dry_run:
        append_log(summary)


if __name__ == "__main__":
    main()
