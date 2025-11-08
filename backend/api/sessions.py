# path: backend/api/sessions.py
# version: v0.31
from fastapi import APIRouter, Depends, HTTPException
import os
import json
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

from backend.db.connection import get_db
from backend.db.models import SessionLog
from backend.dev_recorder import _get_commit_hash, _get_env_snapshot

router = APIRouter(prefix="/api")

LOGS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")

# Pydantic Models (Schemas)
class SessionLogCreate(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_input: str
    final_output: str
    evaluation_score: Optional[float] = None
    evaluation_comment: Optional[str] = None
    workflow_trace: Optional[List[Dict[str, Any]]] = None

class SessionEvaluationUpdate(BaseModel):
    evaluation_score: Optional[float]
    evaluation_comment: Optional[str]

class SessionLogResponse(BaseModel):
    id: str
    created_at: datetime
    user_input: str
    final_output: str
    evaluation_score: Optional[float] = None
    evaluation_comment: Optional[str] = None
    workflow_trace: Optional[List[Dict[str, Any]]] = None

    class Config:
        orm_mode = True

# API Endpoints
@router.get("/sessions", response_model=List[SessionLogResponse])
async def get_sessions(db: Session = Depends(get_db)):
    """Fetches all session logs, ordered by most recent first."""
    sessions = db.query(SessionLog).order_by(desc(SessionLog.created_at)).all()
    return sessions

@router.get("/sessions/{session_id}", response_model=SessionLogResponse)
async def get_session(session_id: str, db: Session = Depends(get_db)):
    """Fetches a single session log by its ID."""
    session = db.query(SessionLog).filter(SessionLog.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.post("/sessions", response_model=SessionLogResponse)
async def create_session_log(session_data: SessionLogCreate, db: Session = Depends(get_db)):
    try:
        db_session_log = SessionLog(**session_data.dict())
        db.add(db_session_log)
        db.commit()
        db.refresh(db_session_log)
        return db_session_log
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create session log: {e}")

@router.patch("/sessions/{session_id}")
async def update_session_evaluation(
    session_id: str,
    evaluation_update: SessionEvaluationUpdate,
    db: Session = Depends(get_db)
):
    session_log = db.query(SessionLog).filter(SessionLog.id == session_id).first()

    if not session_log:
        raise HTTPException(status_code=404, detail="Session not found")

    update_data = evaluation_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(session_log, key, value)

    try:
        db.commit()
        db.refresh(session_log)
        log_evaluation_event(
            session_id=str(session_id),
            score=session_log.evaluation_score,
            comment=session_log.evaluation_comment,
        )
        return {"message": "Session evaluation updated and logged successfully", "session_id": session_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update session evaluation: {e}")

# Helper function for logging
def log_evaluation_event(session_id: str, score: Optional[float], comment: Optional[str], ai_comment: str = "Feedback received."):
    """評価イベントを /logs/evaluation_*.json として保存"""
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_id = f"evaluation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    entry = {
        "id": log_id,
        "timestamp": datetime.utcnow().isoformat(),
        "type": "evaluation_feedback",
        "context": {"session_id": session_id},
        "output": {"score": score, "comment": comment},
        "commit_hash": _get_commit_hash(),
        "env_snapshot": _get_env_snapshot(),
        "ai_comment": ai_comment
    }
    path = os.path.join(LOGS_DIR, f"{log_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)
    print(f"📝 Evaluation feedback logged: {path}")
