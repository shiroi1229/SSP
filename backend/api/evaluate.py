from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional
# from orchestrator.main import run_orchestrator_workflow # Temporarily disabled for v2.2 refactoring
from backend.db.connection import SessionLocal
from backend.db.models import SessionLog
from sqlalchemy.orm import Session

import traceback

router = APIRouter(prefix="/api", tags=["Evaluation"])

class EvaluationRequest(BaseModel):
    session_id: str
    evaluation_score: int = Field(..., ge=1, le=5)
    evaluation_comment: Optional[str] = Field(None, max_length=500)
    question: str

@router.post("/evaluate")
async def evaluate_session(request: EvaluationRequest):
    """
    Saves session evaluation to the database. Regeneration feature is temporarily disabled.
    """
    db: Session = SessionLocal()
    try:
        session_log = db.query(SessionLog).filter(SessionLog.id == request.session_id).first()
        if not session_log:
            raise HTTPException(status_code=404, detail="Session not found.")

        session_log.evaluation_score = request.evaluation_score
        session_log.evaluation_comment = request.evaluation_comment
        db.commit()
        db.refresh(session_log)

        response_message = "Feedback saved successfully."
        new_answer = None

        # --- Regeneration Disabled in v2.2 ---
        # if request.evaluation_score <= 3:
        #     print(f"Low score ({request.evaluation_score}) detected, triggering regeneration.")
        #     final_output, _ = run_orchestrator_workflow(user_input=request.question, interactive_feedback=False)
        #     new_answer = final_output
        #     response_message = "Feedback saved and regeneration executed."
        #     print(f"Regeneration complete. New answer: {new_answer}")

        return {
            "status": "ok", 
            "message": response_message, 
            "new_answer": new_answer, 
            "updated_evaluation_score": session_log.evaluation_score, 
            "updated_evaluation_comment": session_log.evaluation_comment
        }
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process evaluation: {e}")
    finally:
        db.close()
