from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import JSONResponse

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

router = APIRouter(prefix="/security", tags=["Security"])


@router.get("/verify")
def verify_security_stack():
    integrity_snapshot = integrity_checker.inspect_channels()
    signatures = [
        quantum_cipher.sign_channel_digest(channel["name"], channel["hash"])
        for channel in integrity_snapshot["channels"]
    ]
    rekey_channels = [channel for channel in integrity_snapshot["channels"] if channel["status"] == "rekeying"]
    rekey_event = None
    if rekey_channels:
        new_key = quantum_cipher.rotate_key()
        rekey_signatures = [
            quantum_cipher.sign_channel_digest(channel["name"], channel["hash"])
            for channel in rekey_channels
        ]
        rekey_event = {
            "rotated_key": new_key,
            "channels": [channel["name"] for channel in rekey_channels],
            "signatures": rekey_signatures,
        }
    zkp_snapshot = zkp_engine.run_proofs(integrity_snapshot["channels"])
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


@router.get("/refresh-log")
def get_refresh_log(limit: int = 5):
    entries = read_recent_refresh_entries(limit=limit)
    auto_retry_info = auto_retry_if_needed(entries)
    return {
        "entries": entries,
        "available": bool(entries),
        "recentFailures": has_recent_failures(entries),
        "failureDetails": recent_failure_details(entries),
        "autoRetry": auto_retry_info,
    }


@router.post("/refresh-run")
def trigger_security_refresh(dry_run: bool = False):
    result = run_refresh(dry_run=dry_run)
    status = 200 if result.get("success") else 500
    return JSONResponse(content=result, status_code=status)
