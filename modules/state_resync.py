"""Helpers to capture and restore system state snapshots."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from backend.db.connection import SessionLocal
from backend.db.models import SessionLog

SNAPSHOT_DIR = Path("state_snapshots")
SNAPSHOT_DIR.mkdir(exist_ok=True)


def capture_state_snapshot() -> dict:
    """Capture recent sessions and cache metadata for Resync."""
    with SessionLocal() as session:
        sessions = (
            session.query(SessionLog)
            .order_by(SessionLog.created_at.desc())
            .limit(50)
            .all()
        )

    snapshot = {
        "timestamp": datetime.utcnow().isoformat(),
        "session_count": len(sessions),
        "sessions": [
            {
                "id": s.id,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "evaluation_score": s.evaluation_score,
                "evaluation_comment": s.evaluation_comment,
            }
            for s in sessions
        ],
    }

    path = SNAPSHOT_DIR / f"state_snapshot_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    snapshot["path"] = str(path)
    return snapshot


def get_latest_snapshot() -> dict | None:
    files = sorted(SNAPSHOT_DIR.glob("state_snapshot_*.json"), reverse=True)
    if not files:
        return None
    try:
        return json.loads(files[0].read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
