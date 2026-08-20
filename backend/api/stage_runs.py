# path: backend/api/stage_runs.py
# version: UI-v2.0
"""
Stage run archive APIs.

Provides read-only access to timeline execution logs produced by StageDirector
so that the Auto Director Console can display past performances.
"""

from pathlib import Path
from typing import List
import json

from fastapi import APIRouter, HTTPException

from modules.log_manager import log_manager

router = APIRouter()

ARCHIVE_DIR = Path("data/stage_runs")


def _load_archive(path: Path) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Stage run not found.")
    except json.JSONDecodeError as exc:
        log_manager.error(f"[StageRuns] Invalid JSON in {path}: {exc}")
        raise HTTPException(status_code=500, detail="Stage run file is corrupted.")


@router.get("/stage/runs", response_model=List[dict])
async def list_stage_runs(limit: int = 25):
    """
    Return a lightweight list of recent stage runs (metadata only).
    """
    if not ARCHIVE_DIR.exists():
        return []

    items: List[dict] = []
    for path in sorted(ARCHIVE_DIR.glob("*.json"), reverse=True):
        data = _load_archive(path)
        meta = data.get("metadata", {})
        items.append({
            "id": path.stem,
            "filename": path.name,
            "label": meta.get("label"),
            "tags": meta.get("tags", []),
            "source_timeline": meta.get("source_timeline"),
            "captured_at": data.get("captured_at") or meta.get("captured_at"),
            "event_count": meta.get("event_count") or len(data.get("log_events", [])),
        })
        if len(items) >= limit:
            break

    return items


@router.get("/stage/runs/{run_id}")
async def get_stage_run(run_id: str):
    """
    Return the full archived payload (timeline + execution log) for a given run ID.
    """
    filename = f"{run_id}.json" if not run_id.endswith(".json") else run_id
    path = ARCHIVE_DIR / filename
    data = _load_archive(path)
    data.setdefault("id", run_id)
    return data
