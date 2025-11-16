from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from modules.log_manager import log_manager
from modules.akashic_integration import collect_akashic_state, persist_akashic_state
from backend.db.connection import get_db, ensure_awareness_snapshot_table
from backend.db.models import AwarenessSnapshot as DBAwarenessSnapshot
from backend.db.schemas import (
    AwarenessSnapshot as AwarenessSnapshotSchema,
    AwarenessSnapshotCreate,
    AkashicIntegrationState,
)

router = APIRouter(prefix="/awareness", tags=["Awareness"])


@router.get("/snapshots", response_model=List[AwarenessSnapshotSchema])
def list_awareness_snapshots(
    limit: int = Query(20, ge=1, le=200, description="Number of snapshots to return"),
    db: Session = Depends(get_db),
):
    ensure_awareness_snapshot_table()
    snapshots = (
        db.query(DBAwarenessSnapshot)
        .order_by(DBAwarenessSnapshot.created_at.desc())
        .limit(limit)
        .all()
    )
    log_manager.debug(f"Fetched {len(snapshots)} awareness snapshots.")
    return snapshots


@router.post("/snapshots", response_model=AwarenessSnapshotSchema)
def create_awareness_snapshot(payload: AwarenessSnapshotCreate, db: Session = Depends(get_db)):
    ensure_awareness_snapshot_table()
    db_snapshot = DBAwarenessSnapshot(
        backend_state=payload.backend_state,
        frontend_state=payload.frontend_state,
        robustness_state=payload.robustness_state,
        awareness_summary=payload.awareness_summary,
        context_vector=payload.context_vector,
    )
    try:
        db.add(db_snapshot)
        db.commit()
        db.refresh(db_snapshot)
        log_manager.info("Stored awareness snapshot via API.")
        return db_snapshot
    except Exception as exc:
        db.rollback()
        log_manager.error(f"Failed to store awareness snapshot: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to store awareness snapshot.")


@router.get("/akashic", response_model=AkashicIntegrationState)
def get_akashic_state(persist: bool = False):
    try:
        state = collect_akashic_state()
        if persist:
            persist_akashic_state(state)
        return state
    except Exception as exc:
        log_manager.error(f"Failed to collect Akashic state: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to collect Akashic state.")
