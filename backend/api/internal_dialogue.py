from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from backend.db.connection import get_db, ensure_internal_dialogue_table
from backend.db.models import InternalDialogue as DBInternalDialogue
from backend.db.schemas import InternalDialogue as InternalDialogueSchema
from modules.internal_dialogue import generate_internal_dialogue
from modules.log_manager import log_manager

router = APIRouter(prefix="/internal-dialogue", tags=["InternalDialogue"])


@router.get("/logs", response_model=List[InternalDialogueSchema])
def list_internal_dialogues(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    ensure_internal_dialogue_table()
    records = (
        db.query(DBInternalDialogue)
        .order_by(DBInternalDialogue.created_at.desc())
        .limit(limit)
        .all()
    )
    return records


@router.post("/generate", response_model=InternalDialogueSchema)
def trigger_internal_dialogue(db: Session = Depends(get_db)):
    ensure_internal_dialogue_table()
    try:
        payload = generate_internal_dialogue()
        record = (
            db.query(DBInternalDialogue)
            .filter(DBInternalDialogue.id == payload["id"])
            .first()
        )
        return record
    except Exception as exc:
        log_manager.error(f"Internal dialogue generation failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate internal dialogue.")
