# path: backend/api/get_sessions.py
# version: v0.30
import os
import json
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, nullslast
from sqlalchemy.orm import Session
from backend.db.connection import get_db
from backend.db.models import SessionLog
from typing import List, Optional

router = APIRouter()

@router.get("/sessions")
def get_sessions(db: Session = Depends(get_db)):
    sessions = db.query(SessionLog).order_by(SessionLog.created_at.desc()).all()
    return sessions
