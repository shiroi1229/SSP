from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.security.integrity_checker import integrity_checker
from backend.security.quantum_cipher import quantum_cipher
from backend.security.zkp_engine import zkp_engine
from backend.security.insight_integrity import insight_integrity
from backend.security.refresh_log import (
    read_recent_refresh_entries,
    has_recent_failures,
    recent_failure_details,
)
from backend.security.refresh_runner import run_refresh, auto_retry_if_needed


class SecurityService:
    def verify_stack(self) -> Dict[str, Any]:
        integrity_snapshot = integrity_checker.inspect_channels()
        signatures = [
            quantum_cipher.sign_channel_digest(channel["name"], channel["hash"])  # type: ignore[index]
            for channel in integrity_snapshot["channels"]
        ]
        rekey_channels = [c for c in integrity_snapshot["channels"] if c["status"] == "rekeying"]
        rekey_event: Optional[Dict[str, Any]] = None
        if rekey_channels:
            new_key = quantum_cipher.rotate_key()
            rekey_signatures = [
                quantum_cipher.sign_channel_digest(channel["name"], channel["hash"])  # type: ignore[index]
                for channel in rekey_channels
            ]
            rekey_event = {
                "rotated_key": new_key,
                "channels": [channel["name"] for channel in rekey_channels],
                "signatures": rekey_signatures,
            }
        zkp_snapshot = zkp_engine.run_proofs(integrity_snapshot["channels"])  # type: ignore[index]
        insight = insight_integrity.summarize(signatures, integrity_snapshot, zkp_snapshot)

        return {
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "quantum_layer": {
                "active_key": quantum_cipher.describe_active_key(),
                "history": quantum_cipher.recent_history(),
                "signatures": signatures,
                "rekey_event": rekey_event,
            },
            "integrity": integrity_snapshot,
            "zkp": zkp_snapshot,
            "insight": insight,
        }

    def get_refresh_log(self, *, limit: int = 5) -> Dict[str, Any]:
        entries = read_recent_refresh_entries(limit=limit)
        auto_retry_info = auto_retry_if_needed(entries)
        return {
            "entries": entries,
            "available": bool(entries),
            "recentFailures": has_recent_failures(entries),
            "failureDetails": recent_failure_details(entries),
            "autoRetry": auto_retry_info,
        }

    def trigger_refresh(self, *, dry_run: bool = False) -> Dict[str, Any]:
        return run_refresh(dry_run=dry_run)
