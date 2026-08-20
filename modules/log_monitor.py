
# path: modules/log_monitor.py
"""Structured contract/log monitoring utilities."""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict
import threading

LOG_PATH = Path("logs/contract_monitor.log")
_lock = threading.Lock()


def _write_event(event: Dict[str, Any]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    event.setdefault("timestamp", datetime.utcnow().isoformat())
    with _lock, LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def log_contract_violation(module_name: str, detail: str, payload: Dict[str, Any] | None = None) -> None:
    event = {
        "type": "contract_violation",
        "module": module_name,
        "detail": detail,
        "payload": payload or {},
    }
    _write_event(event)


def log_recovery_action(module_name: str, action: str, payload: Dict[str, Any] | None = None) -> None:
    event = {
        "type": "recovery_action",
        "module": module_name,
        "action": action,
        "payload": payload or {},
    }
    _write_event(event)


def log_info(event_type: str, info: Dict[str, Any]) -> None:
    event = {"type": event_type, **info}
    _write_event(event)
