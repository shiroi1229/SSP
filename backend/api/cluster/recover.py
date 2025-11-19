"""Cluster recovery controller for R-v0.5."""

from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.cluster.recovery_agent import recovery_agent
from backend.cluster.sync_manager import sync_manager
from modules.log_manager import log_manager


class RecoveryCommand(BaseModel):
    node: str
    action: Literal["promote", "heal", "sync"]
    target: Optional[str] = None


router = APIRouter(tags=["Cluster"], prefix="/api/cluster")


@router.post("/recover")
def recover_node(payload: RecoveryCommand):
    log_manager.info("[ClusterRecover] Received recovery command", extra={"node": payload.node, "action": payload.action})
    if payload.action == "promote":
        return recovery_agent.promote(payload.node)
    if payload.action == "heal":
        return recovery_agent.heal(payload.node)
    if payload.action == "sync":
        return sync_manager.sync(payload.node)
    raise HTTPException(status_code=400, detail="Unsupported recovery action.")
