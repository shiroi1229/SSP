# path: backend/api/get_session_detail.py
# version: v0.30
import os
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.connection import get_db
from backend.db.models import SessionLog

router = APIRouter()

@router.get("/sessions/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(SessionLog).filter(SessionLog.id == session_id).first()
    if not session:
        return {"error": "Session not found"}
    return {
        "id": session.id,
        "created_at": session.created_at,
        "user_input": session.user_input,
        "final_output": session.final_output,
        "evaluation_score": session.evaluation_score,
        "evaluation_comment": session.evaluation_comment,
        "workflow_trace": session.workflow_trace,
    }
