from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

router = APIRouter()

SNAPSHOT_DIR = Path("data/context_snapshots")
SNAPSHOT_INDEX_FILE = SNAPSHOT_DIR / "snapshots.json"
DEFAULT_PERSONA_STATE = {
    "emotion": "Curious",
    "harmony": 0.75,
    "focus": 0.88,
}

Snapshot = Dict[str, Any]


def _load_snapshot_index() -> List[Snapshot]:
    if not SNAPSHOT_INDEX_FILE.exists():
        raise HTTPException(status_code=404, detail="Context snapshot index not found.")

    try:
        with SNAPSHOT_INDEX_FILE.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Context snapshot index is corrupted.") from exc

    if not isinstance(data, list):
        raise HTTPException(status_code=500, detail="Context snapshot index has invalid format.")

    return data


def _sorted_snapshot_index() -> List[Snapshot]:
    return sorted(_load_snapshot_index(), key=lambda snap: snap.get("created_at", ""), reverse=True)


def _get_snapshot_entry(snapshot_id: str) -> Optional[Snapshot]:
    for entry in _sorted_snapshot_index():
        if entry.get("id") == snapshot_id:
            return entry
    return None


def _load_snapshot_detail(snapshot_id: str) -> Snapshot:
    detail_path = SNAPSHOT_DIR / f"{snapshot_id}.json"
    if detail_path.exists():
        try:
            with detail_path.open(encoding="utf-8") as fh:
                detail = json.load(fh)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=500, detail="Snapshot file is corrupted.") from exc

        if isinstance(detail, dict):
            return detail
        raise HTTPException(status_code=500, detail="Snapshot file contains invalid structure.")

    entry = _get_snapshot_entry(snapshot_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Snapshot not found.")
    return entry


def _latest_snapshot() -> Snapshot:
    snapshots = _sorted_snapshot_index()
    if not snapshots:
        raise HTTPException(status_code=404, detail="No context snapshots available.")
    return snapshots[0]


def _extract_persona_state(snapshot: Snapshot) -> Dict[str, Any]:
    persona_state = DEFAULT_PERSONA_STATE.copy()
    short_term = snapshot.get("short_term") or {}
    candidate = short_term.get("persona_state")
    if isinstance(candidate, dict):
        persona_state.update({k: candidate.get(k, persona_state[k]) for k in DEFAULT_PERSONA_STATE})
        return persona_state

    for key in DEFAULT_PERSONA_STATE:
        value = short_term.get(key)
        if isinstance(value, (int, float)) and key in {"harmony", "focus"}:
            persona_state[key] = float(value)
        elif isinstance(value, str) and key == "emotion":
            persona_state[key] = value

    return persona_state


@router.get("/context/state")
async def get_context_state():
    """Provides the latest snapshot in the legacy context-state shape."""

    latest_snapshot = _latest_snapshot()
    persona_state = _extract_persona_state(latest_snapshot)
    evaluation_score = (
        latest_snapshot.get("mid_term", {}).get("evaluation_score")
        or latest_snapshot.get("evaluation_score")
        or 0.0
    )
    generated_output = (
        latest_snapshot.get("generated_output")
        or latest_snapshot.get("short_term", {}).get("prompt")
        or "最新スナップショットから生成された出力はまだ記録されていません。"
    )

    cognitive_harmony = {
        "score": round(float(persona_state.get("harmony", 0.0)) * 100),
        "emotion": persona_state.get("emotion", "Unknown"),
    }

    introspection_logs = latest_snapshot.get("introspection_logs") or []

    return {
        "personaState": persona_state,
        "cognitiveHarmony": cognitive_harmony,
        "introspectionLogs": introspection_logs,
        "evaluationScore": evaluation_score,
        "generatedOutput": generated_output,
    }


@router.get("/context/snapshots")
async def list_context_snapshots():
    """Returns the recorded snapshot summaries."""

    return {"snapshots": _sorted_snapshot_index()}


@router.get("/context/snapshots/{snapshot_id}")
async def get_context_snapshot(snapshot_id: str):
    """Returns a specific snapshot, falling back to the summary entry."""

    return _load_snapshot_detail(snapshot_id)
