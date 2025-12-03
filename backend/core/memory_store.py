# path: backend/core/memory_store.py
# version: v0.1
# purpose: SQLAlchemy-backed MemoryStore implementation centralizing DB writes

from __future__ import annotations

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.db.connection import SessionLocal, save_session_to_db
from backend.db.models import SessionLog, DevLog
from fastapi import HTTPException
import uuid

from backend.core.interfaces import MemoryStore


class SqlAlchemyMemoryStore(MemoryStore):
    def __init__(self) -> None:
        # No global state; sessions are per-operation
        pass

    def _session(self) -> Session:
        return SessionLocal()

    def save(self, record_data: Dict[str, Any], iteration: int = 1) -> None:
        payload = dict(record_data)
        payload.setdefault("iteration", iteration)
        save_session_to_db(payload)

    def save_record_to_db(self, log_data: Dict[str, Any]) -> None:
        save_session_to_db(dict(log_data))

    def save_evaluation(self, *, session_id: str, score: int, comment: Optional[str]) -> Dict[str, Any]:
        db: Session = self._session()
        try:
            session_log = db.query(SessionLog).filter(SessionLog.id == session_id).first()
            if not session_log:
                raise HTTPException(status_code=404, detail="Session not found")
            session_log.evaluation_score = score
            session_log.evaluation_comment = comment
            db.commit()
            db.refresh(session_log)
            return {
                "session_id": session_id,
                "updated_evaluation_score": session_log.evaluation_score,
                "updated_evaluation_comment": session_log.evaluation_comment,
            }
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def save_meta_feedback(self, payload: Dict[str, Any]) -> None:
        # Placeholder for persistence of meta feedback summaries/results if needed.
        # In this phase, no-op to avoid altering DB schema; keep in orchestrator context.
        return None

    def save_auto_action(self, action: Dict[str, Any], success: Optional[bool]) -> None:
        db: Session = self._session()
        try:
            entry = DevLog(
                id=str(uuid.uuid4()).replace('-', ''),
                type="auto_action",
                summary=(action.get("type") or "auto_action"),
                file_path="auto_action",
                tags={"success": bool(success) if success is not None else True},
                execution_trace={"action": action},
                author="system",
            )
            db.add(entry)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
