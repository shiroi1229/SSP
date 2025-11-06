# path: backend/api/post_session.py
# version: v0.30
from fastapi import APIRouter, Depends, HTTPException
import os
import json
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

from backend.db.connection import get_db
from backend.db.models import SessionLog
from backend.dev_recorder import _get_commit_hash, _get_env_snapshot
# from orchestrator.feedback_loop_integration import adaptive_regeneration # TODO: Re-implement with v2.4 Context Evolution Framework

router = APIRouter()

LOGS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")

def log_evaluation_event(session_id: str, score: float, comment: str, ai_comment: str = "Feedback received."):
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

class FeedbackSchema(BaseModel):
    score: float
    comment: str
    answer: Optional[str] = None

class WorkflowTraceEntrySchema(BaseModel):
    module: str
    status: Optional[str] = None
    context: Optional[Any] = None # Can be string or array of objects
    answer_str: Optional[str] = None
    rating: Optional[int] = None
    feedback: Optional[str] = None

class SessionLogCreate(BaseModel):
    created_at: datetime = datetime.utcnow() # Changed from timestamp to created_at
    user_input: str
    final_output: str
    evaluation_score: Optional[float] = None
    evaluation_comment: Optional[str] = None
    workflow_trace: Optional[List[Dict[str, Any]]] = None # Use List[Dict[str, Any]] for flexibility

class SessionEvaluationUpdate(BaseModel):
    evaluation_score: Optional[float]  # ← floatに変更
    evaluation_comment: Optional[str]  # ← 任意に変更（空欄も許可）

@router.post("/sessions")
async def create_session_log(session_data: SessionLogCreate, db: Session = Depends(get_db)):
    try:
        db_session_log = SessionLog(
            created_at=session_data.created_at, # Changed from timestamp to created_at
            user_input=session_data.user_input,
            final_output=session_data.final_output,
            evaluation_score=session_data.evaluation_score,
            evaluation_comment=session_data.evaluation_comment,
            workflow_trace=session_data.workflow_trace # SQLAlchemy's JSON type handles dicts/lists
        )
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

    session_log.evaluation_score = evaluation_update.evaluation_score
    session_log.evaluation_comment = evaluation_update.evaluation_comment

    regenerated_output = None
    # TODO: Re-implement adaptive regeneration using the v2.4 Context Evolution Framework
    # if evaluation_update.evaluation_score is not None and evaluation_update.evaluation_score <= 3:
    #     print(f"💡 Evaluation score {evaluation_update.evaluation_score} <= 3. Triggering adaptive regeneration...")
    #     regenerated_output = adaptive_regeneration(
    #         session_id=session_id,
    #         user_input=session_log.user_input, # Retrieve user_input from session_log
    #         score=evaluation_update.evaluation_score,
    #         comment=evaluation_update.evaluation_comment
    #     )
    #     if regenerated_output:
    #         session_log.final_output = regenerated_output
    #         # Append adaptive regeneration event to workflow_trace
    #         if session_log.workflow_trace is None:
    #             session_log.workflow_trace = []
    #         session_log.workflow_trace.append({
    #             "module": "adaptive_regeneration",
    #             "status": "completed",
    #             "score": evaluation_update.evaluation_score,
    #             "strategy": "dynamic_prompt_and_temperature_adjustment", # This could be more detailed
    #             "new_output": regenerated_output,
    #             "timestamp": datetime.utcnow().isoformat()
    #         })

    try:
        db.commit()
        db.refresh(session_log)
        # ✅ JSONロギングを追加
        log_evaluation_event(
            session_id=str(session_id),
            score=evaluation_update.evaluation_score,
            comment=evaluation_update.evaluation_comment,
            regenerated_output=regenerated_output # Pass regenerated_output to log
        )
        return {"message": "Session evaluation updated and logged successfully", "session_id": session_id, "regenerated_output": regenerated_output}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update session evaluation: {e}")

def log_evaluation_event(session_id: str, score: float, comment: str, ai_comment: str = "Feedback received.", regenerated_output: Optional[str] = None):
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
    if regenerated_output:
        entry["adaptive_context"] = {"regenerated_output": regenerated_output}
    path = os.path.join(LOGS_DIR, f"{log_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)
    print(f"📝 Evaluation feedback logged: {path}")
