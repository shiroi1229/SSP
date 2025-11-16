"""Utilities to trigger the security refresh script (manual or auto-retry)."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any

SCRIPT_PATH = Path("scripts/refresh_security_sources.py")
AUTO_RETRY_INTERVAL = 600  # seconds
_last_auto_retry: float = 0.0


def run_refresh(dry_run: bool = False) -> Dict[str, Any]:
    cmd = [sys.executable, str(SCRIPT_PATH)]
    if dry_run:
        cmd.append("--dry-run")
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception as exc:  # pragma: no cover
        return {"success": False, "error": str(exc)}

    return {
        "success": completed.returncode == 0,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "returncode": completed.returncode,
    }


def auto_retry_if_needed(entries: list[dict], window: int = 3) -> Dict[str, Any] | None:
    global _last_auto_retry
    if not entries:
        return None
    failures = [entry for entry in entries[-window:] if entry.get("errors")]
    if not failures:
        return None
    now = time.time()
    if now - _last_auto_retry < AUTO_RETRY_INTERVAL:
        return {"triggered": False, "reason": "interval"}
    result = run_refresh(dry_run=False)
    _last_auto_retry = now
    return {"triggered": True, "result": result}
