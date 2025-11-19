from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.connection import get_db
from backend.db.models import AwarenessSnapshot, InternalDialogue

router = APIRouter(prefix="/awareness", tags=["Awareness"])


@router.get("/insights")
def get_awareness_insights(db: Session = Depends(get_db)):
    """
    Provide the latest awareness snapshot together with recent internal dialogue.
    """
    snapshot = (
        db.query(AwarenessSnapshot)
        .order_by(AwarenessSnapshot.created_at.desc())
        .first()
    )
    dialogues = (
        db.query(InternalDialogue)
        .order_by(InternalDialogue.created_at.desc())
        .limit(4)
        .all()
    )
    return {
        "snapshot": {
            "created_at": snapshot.created_at.isoformat() if snapshot else None,
            "awareness_summary": snapshot.awareness_summary if snapshot else None,
            "backend_state": snapshot.backend_state if snapshot else {},
            "frontend_state": snapshot.frontend_state if snapshot else {},
            "robustness_state": snapshot.robustness_state if snapshot else {},
            "context_vector": snapshot.context_vector if snapshot else {},
        },
        "dialogues": [
            {
                "id": dialogue.id,
                "created_at": dialogue.created_at.isoformat(),
                "participants": dialogue.participants,
                "transcript": dialogue.transcript,
                "insights": dialogue.insights,
            }
            for dialogue in dialogues
        ],
    }
