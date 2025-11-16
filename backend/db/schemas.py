# path: backend/db/schemas.py
# version: v1

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any, Union

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
    developmentInstruction: Optional[Any] = Field(None, alias="development_details") # Changed to Any
    parent_id: Optional[int] = None

class RoadmapItemUpdateByVersion(BaseModel):
    developmentInstruction: Optional[str] = Field(None, alias="development_details")
    parent_id: Optional[int] = None
    status: Optional[str] = None
    progress: Optional[int] = None
    keyFeatures: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    metrics: Optional[List[str]] = None

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
    Awareness_Engine: List[RoadmapItem] = []

class RoadmapPrefixSummary(BaseModel):
    prefix: str
    count: int
    completed: int
    in_progress: int
    not_started: int

class RoadmapDelayedItem(BaseModel):
    version: str
    codename: str
    progress: Optional[int] = None
    status: Optional[str] = None

class RoadmapStatsResponse(BaseModel):
    summary: List[RoadmapPrefixSummary]
    delayed: List[RoadmapDelayedItem]


class AwarenessSnapshotBase(BaseModel):
    created_at: datetime
    backend_state: Optional[Dict[str, Any]] = None
    frontend_state: Optional[Dict[str, Any]] = None
    robustness_state: Optional[Dict[str, Any]] = None
    awareness_summary: Optional[str] = None
    context_vector: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class AwarenessSnapshotCreate(BaseModel):
    backend_state: Optional[Dict[str, Any]] = None
    frontend_state: Optional[Dict[str, Any]] = None
    robustness_state: Optional[Dict[str, Any]] = None
    awareness_summary: Optional[str] = None
    context_vector: Optional[Dict[str, Any]] = None


class AwarenessSnapshot(AwarenessSnapshotBase):
    id: int


class InternalDialogueBase(BaseModel):
    created_at: datetime
    participants: Optional[List[str]] = None
    transcript: Optional[List[Dict[str, Any]]] = None
    insights: Optional[str] = None
    source_snapshot_id: Optional[int] = None
    meta: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class InternalDialogueCreate(BaseModel):
    participants: Optional[List[str]] = None
    transcript: Optional[List[Dict[str, Any]]] = None
    insights: Optional[str] = None
    source_snapshot_id: Optional[int] = None
    meta: Optional[Dict[str, Any]] = None


class InternalDialogue(InternalDialogueBase):
    id: int


class AkashicIntegrationState(BaseModel):
    collected_at: datetime
    snapshot: Optional[AwarenessSnapshot] = None
    internal_dialogue: Optional[InternalDialogue] = None
    akashic_sync: Dict[str, Any]
    persona_state: Dict[str, Any]
