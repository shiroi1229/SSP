# path: backend/core/di.py
# version: v0.1
# purpose: FastAPI DI providers for orchestrator service and dependencies（app.state経由の取得ユーティリティ含む）

from __future__ import annotations

from functools import lru_cache

from backend.core.memory_store import SqlAlchemyMemoryStore
from fastapi import Request
from backend.core.orchestrator_service import OrchestratorService
from backend.core.services.knowledge_service import KnowledgeService
from backend.core.services.security_service import SecurityService
from backend.core.services.stage_service import StageService
from orchestrator.context_manager import ContextManager
from orchestrator.recovery_policy_manager import RecoveryPolicyManager


@lru_cache(maxsize=1)
def get_memory_store() -> SqlAlchemyMemoryStore:
    # Stateless provider; DB sessions are scoped per call inside the store
    return SqlAlchemyMemoryStore()


def get_orchestrator_service() -> OrchestratorService:
    return OrchestratorService(
        memory_store=get_memory_store(),
        knowledge=KnowledgeService(),
        security=SecurityService(),
        stage=StageService(),
    )


_ctx_singleton: ContextManager | None = None
_insight_singleton: object | None = None


def get_context_manager() -> ContextManager:
    global _ctx_singleton
    if _ctx_singleton is None:
        _ctx_singleton = ContextManager()
    return _ctx_singleton


def get_insight_monitor():
    global _insight_singleton
    if _insight_singleton is None:
        # Lazy import to avoid circular import with modules.auto_action_log -> backend.core.di
        from orchestrator.insight_monitor import InsightMonitor
        # Default to read-only (no side effects) for API usage; orchestrator can override.
        _insight_singleton = InsightMonitor(get_context_manager(), RecoveryPolicyManager(), allow_side_effects=False)
    return _insight_singleton


# Preferred (no globals) accessors via app.state
def get_app_context_manager(request: Request) -> ContextManager:
    return request.app.state.context_manager


def get_app_insight_monitor(request: Request):
    return request.app.state.insight_monitor
