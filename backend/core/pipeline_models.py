# path: backend/core/pipeline_models.py
# version: v0.1
# purpose: オーケストレータの型安全なデータフローモデル定義（Pydantic v2）

from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict


class RequestCtx(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: Optional[str] = None
    user_input: Optional[str] = None
    metadata: Optional[dict] = None


class RetrievalResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: List[dict]
    total: int


class RerankResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: List[dict]


class Generated(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str
    meta: Optional[dict] = None


class Evaluated(BaseModel):
    model_config = ConfigDict(extra="forbid")
    score: Optional[float] = None
    comment: Optional[str] = None


class Persisted(BaseModel):
    model_config = ConfigDict(extra="forbid")
    record_id: Optional[str] = None
    snapshot: Optional[dict] = None
