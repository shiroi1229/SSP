"""Akashic Integration utilities for A-v4.0."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from backend.db.connection import SessionLocal
from backend.db.models import AwarenessSnapshot, InternalDialogue
from backend.db.schemas import AwarenessSnapshot as AwarenessSnapshotSchema
from backend.db.schemas import InternalDialogue as InternalDialogueSchema
from modules.akashic_sync_manager import manager as akashic_sync_manager
from modules.persona_manager import get_current_persona_state
from orchestrator.context_manager import ContextManager
from modules.log_manager import log_manager

AKASHIC_HISTORY_DIR = Path("logs/context_evolution")
CONTEXT_HISTORY_PATH = "logs/context_history.json"


def _latest_awareness_snapshot(session) -> AwarenessSnapshot | None:
    return (
        session.query(AwarenessSnapshot)
        .order_by(AwarenessSnapshot.created_at.desc())
        .first()
    )


def _latest_internal_dialogue(session) -> InternalDialogue | None:
    return (
        session.query(InternalDialogue)
        .order_by(InternalDialogue.created_at.desc())
        .first()
    )


def collect_akashic_state() -> Dict[str, Any]:
    """Collects the latest Awareness + Dialogue + Akashic Sync + Persona data."""
    session = SessionLocal()
    try:
        snapshot = _latest_awareness_snapshot(session)
        dialogue = _latest_internal_dialogue(session)
    finally:
        session.close()

    snapshot_data = (
        AwarenessSnapshotSchema.model_validate(snapshot).model_dump()
        if snapshot
        else None
    )
    dialogue_data = (
        InternalDialogueSchema.model_validate(dialogue).model_dump()
        if dialogue
        else None
    )

    persona_state = asyncio.run(get_current_persona_state())
    akashic_sync_state = akashic_sync_manager.get_state()

    raw_state = {
        "collected_at": datetime.utcnow().isoformat(),
        "snapshot": snapshot_data,
        "internal_dialogue": dialogue_data,
        "akashic_sync": akashic_sync_state,
        "persona_state": persona_state,
    }
    return json.loads(json.dumps(raw_state, default=str))


def persist_akashic_state(state: Dict[str, Any]) -> None:
    """Persist the Akashic state to context history and snapshot logs."""
    manager = ContextManager(history_path=CONTEXT_HISTORY_PATH)
    manager.set("long_term.akashic_state", state, reason="Akashic integration update")
    manager.add_to_history("akashic_state", state)

    AKASHIC_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    filename = AKASHIC_HISTORY_DIR / f"akashic_state_{state['collected_at'].replace(':', '-')}.json"
    filename.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    log_manager.info(f"[AkashicIntegration] Persisted state to {filename}")


def collect_and_persist_akashic_state() -> Dict[str, Any]:
    state = collect_akashic_state()
    persist_akashic_state(state)
    return state
