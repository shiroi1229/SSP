from fastapi import APIRouter
from pydantic import BaseModel, Field

from modules.context_rollback import rollback_manager

router = APIRouter(prefix="/context", tags=["Context"])


class RollbackRequest(BaseModel):
    timestamp: str | None = Field(default=None, description="ISO8601 timestamp to target.")
    reason: str = Field(default="manual rollback")


@router.post("/rollback")
def rollback_context(request: RollbackRequest):
    return rollback_manager.rollback(request.timestamp, request.reason)
