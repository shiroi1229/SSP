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
        from_attributes = True # Changed from orm_mode to from_attributes for Pydantic v2

class SessionLogCreate(SessionLogBase):
    pass

class SessionLog(SessionLogBase):
    pass

class RoadmapItemBase(BaseModel):
    version: str
    codename: str
    goal: str
    status: str # "✅" | "🔄" | "⚪"
    description: str
    startDate: Optional[str] = None # YYYY-MM-DD
    endDate: Optional[str] = None   # YYYY-MM-DD
    progress: Optional[int] = None  # 0-100 percentage
    keyFeatures: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    metrics: Optional[List[str]] = None
    owner: Optional[str] = None
    documentationLink: Optional[str] = None
    prLink: Optional[str] = None

class RoadmapItemCreate(RoadmapItemBase):
    pass

class RoadmapItem(RoadmapItemBase):
    id: int

    class Config:
        from_attributes = True

class RoadmapData(BaseModel):
    backend: List[RoadmapItem]
    frontend: List[RoadmapItem]
    robustness: List[RoadmapItem]
