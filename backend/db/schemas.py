# path: backend/db/schemas.py
# version: v1

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

class SessionLogBase(BaseModel):
    id: str
    created_at: datetime
    user_input: str
    final_output: str
    evaluation_score: Optional[float]
    evaluation_comment: Optional[str]
    workflow_trace: Optional[Dict[str, Any]]
    context: Optional[str]
    generator_prompt: Optional[str]
    generator_response: Optional[str]
    commit_hash: Optional[str]
    env_snapshot: Optional[str]
    ai_comment: Optional[str]

    class Config:
        orm_mode = True

class SessionLogCreate(SessionLogBase):
    pass

class SessionLog(SessionLogBase):
    pass
