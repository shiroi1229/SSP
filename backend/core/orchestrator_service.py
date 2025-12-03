# path: backend/core/orchestrator_service.py
# version: v0.1
# purpose: Thin application service exposing orchestrator use-cases for API layer (evaluation, meta feedback)

from __future__ import annotations

from typing import Dict, Any, Optional

from orchestrator.context_manager import ContextManager
from orchestrator.main import run_context_evolution_cycle
from modules.log_manager import log_manager
from modules.meta_causal_feedback import run_feedback as run_meta_causal_feedback

from backend.core.pipeline_models import RequestCtx
from backend.core.interfaces import MemoryStore
from backend.core.services.governor_service import GovernorService
from backend.core.services.knowledge_service import KnowledgeService
from backend.core.services.rag_pipeline_service import (
    RAGPipelineResult,
    RAGPipelineService,
)
from backend.core.services.security_service import SecurityService
from backend.core.services.stage_service import StageService


class OrchestratorService:
    def __init__(
        self,
        memory_store: MemoryStore,
        knowledge: Optional[KnowledgeService] = None,
        governor: Optional[GovernorService] = None,
        rag_pipeline: Optional[RAGPipelineService] = None,
        security: Optional[SecurityService] = None,
        stage: Optional[StageService] = None,
    ) -> None:
        self._memory_store = memory_store
        self._knowledge = knowledge or KnowledgeService()
        self._governor = governor or GovernorService()
        self._rag_pipeline = rag_pipeline or RAGPipelineService(memory_store=memory_store)
        self._security = security or SecurityService()
        self._stage = stage or StageService()

    def handle_evaluation(self, *, session_id: str, score: int, comment: Optional[str], question: str) -> Dict[str, Any]:
        """Save evaluation via MemoryStore. Regeneration is intentionally not triggered here."""
        saved = self._memory_store.save_evaluation(session_id=session_id, score=score, comment=comment)
        log_manager.info(f"Evaluation saved for session {session_id} with score={score}")
        # Maintain API contract: include message/new_answer keys if clients rely on them, but in 'data'.
        return {
            **saved,
            "message": "Feedback saved successfully.",
            "new_answer": None,
        }

    def run_meta_feedback(self, *, limit: int, threshold: float) -> Dict[str, Any]:
        """Run meta-causal feedback using an ephemeral ContextManager; persist results if needed."""
        context = ContextManager()
        result = run_meta_causal_feedback(context_manager=context, limit=limit, threshold=threshold)
        if result.get("success"):
            # Optional persistence hook
            try:
                self._memory_store.save_meta_feedback({
                    "summary": result.get("summary"),
                    "bias_report": result.get("bias_report"),
                    "optimizer": result.get("optimizer"),
                })
            except Exception as e:
                log_manager.warning(f"save_meta_feedback failed: {e}")
        return result

    def governor_decide(
        self,
        *,
        error_info: Dict[str, Any],
        file_path: str,
        confidence_threshold: float = 0.8,
    ) -> Dict[str, Any]:
        """Run governor pipeline via service facade and return structured result."""
        outcome = self._governor.run(
            error_info=error_info,
            file_path=file_path,
            confidence_threshold=confidence_threshold,
        )
        return outcome.model_dump()

    def run_rag_pipeline(self, request: RequestCtx) -> Dict[str, Any]:
        """Execute the canonical orchestrated RAG pipeline."""
        result: RAGPipelineResult = self._rag_pipeline.run_pipeline(request)
        return result.model_dump()

    def run_chat_cycle(self, *, user_input: str, history: Optional[list[dict]] = None) -> str:
        """Execute the primary orchestrator chat workflow and return raw answer text."""
        answer = run_context_evolution_cycle(user_input, history=history)
        if isinstance(answer, str):
            return answer
        return ""

    # Knowledge
    def list_knowledge(self, *, limit: int, offset: int, order_by: str, descending: bool, source_filter: Optional[str]) -> Dict[str, Any]:
        return self._knowledge.list_knowledge(
            limit=limit,
            offset=offset,
            order_by=order_by,
            descending=descending,
            source_filter=source_filter,
        )

    def search_knowledge(self, *, query: str, limit: int, offset: int, order_by: str, descending: bool, source_filter: Optional[str]) -> Dict[str, Any]:
        return self._knowledge.search_knowledge(
            query=query,
            limit=limit,
            offset=offset,
            order_by=order_by,
            descending=descending,
            source_filter=source_filter,
        )

    def knowledge_detail(self, *, id: str) -> Optional[Dict[str, Any]]:
        return self._knowledge.get_detail(id=id)

    def add_knowledge(
        self,
        *,
        text: str,
        title: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self._knowledge.add_entry(text=text, title=title, source=source, metadata=metadata)

    # Security
    def verify_security(self) -> Dict[str, Any]:
        return self._security.verify_stack()

    def get_security_refresh_log(self, *, limit: int = 5) -> Dict[str, Any]:
        return self._security.get_refresh_log(limit=limit)

    def trigger_security_refresh(self, *, dry_run: bool = False) -> Dict[str, Any]:
        return self._security.trigger_refresh(dry_run=dry_run)

    # Stage
    async def stage_play(self) -> Dict[str, Any]:
        return await self._stage.play()

    def stage_health(self) -> Dict[str, Any]:
        return self._stage.health()

    async def stage_stop(self) -> Dict[str, Any]:
        return await self._stage.stop()

    def stage_timeline(self) -> Dict[str, Any]:
        return self._stage.get_timeline()

    # Stage WS hooks
    def stage_ws_connect(self, ws: Any) -> None:  # type: ignore[name-defined]
        self._stage.add_ws(ws)

    def stage_ws_disconnect(self, ws: Any) -> None:  # type: ignore[name-defined]
        self._stage.remove_ws(ws)
