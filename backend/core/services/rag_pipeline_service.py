# path: backend/core/services/rag_pipeline_service.py
# version: v0.1
# purpose: Encapsulate the canonical RAG → generation → evaluation → persistence pipeline

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from backend.core.pipeline_models import (
    Evaluated,
    Generated,
    Persisted,
    RequestCtx,
    RetrievalResult,
)
from modules.log_manager import log_manager
from modules.rag_engine import RAGEngine as LegacyRAGEngine
from modules.rag_formatter import build_context_text

from backend.core.interfaces import Evaluator, Generator, MemoryStore, RagEngine as RagEngineProtocol
from backend.core.services.pipeline_adapters import (
    ContextEvaluatorAdapter,
    ContextGeneratorAdapter,
    FileMemoryStoreAdapter,
)
from orchestrator.context_manager import ContextManager


class RAGPipelineResult(BaseModel):
    """Typed summary of an entire RAG pipeline execution."""

    request: RequestCtx
    retrieval: RetrievalResult
    generated: Generated
    evaluation: Evaluated
    persisted: Persisted


class PipelineMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    history: Optional[List[dict]] = None
    model_params: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
    iteration: Optional[int] = None
    regeneration: Optional[bool] = None


class RAGPipelineService:
    """One-directional orchestration of the canonical RAG pipeline."""

    def __init__(
        self,
        *,
        rag_engine: Optional[RagEngineProtocol] = None,
        generator: Optional[Generator] = None,
        evaluator: Optional[Evaluator] = None,
        memory_store: Optional[MemoryStore] = None,
        retrieval_top_k: int = 5,
    ) -> None:
        self._rag_engine = rag_engine or LegacyRAGEngine()
        self._generator = generator or ContextGeneratorAdapter()
        self._evaluator = evaluator or ContextEvaluatorAdapter()
        self._memory_store = memory_store or FileMemoryStoreAdapter()
        self._retrieval_top_k = retrieval_top_k

    def run_pipeline(self, request: RequestCtx) -> RAGPipelineResult:
        """Execute the full pipeline and return typed results."""

        if not request.user_input:
            raise ValueError("RequestCtx.user_input is required for the RAG pipeline")

        session_id = request.session_id or str(uuid4())
        metadata = PipelineMetadata.model_validate(request.metadata or {})
        normalized_request = request.model_copy(update={"session_id": session_id})

        context_manager = ContextManager()
        self._seed_context(context_manager, normalized_request, metadata)

        retrieval = self._run_retrieval(context_manager, normalized_request)
        generated = self._run_generation(context_manager)
        evaluation = self._run_evaluation(context_manager)
        persisted = self._persist_results(
            session_id=session_id,
            request=normalized_request,
            generated=generated,
            evaluation=evaluation,
            metadata=metadata,
        )

        return RAGPipelineResult(
            request=normalized_request,
            retrieval=retrieval,
            generated=generated,
            evaluation=evaluation,
            persisted=persisted,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _seed_context(
        self,
        context_manager: ContextManager,
        request: RequestCtx,
        metadata: PipelineMetadata,
    ) -> None:
        context_manager.set("short_term.session_id", request.session_id, reason="Pipeline initialization")
        context_manager.set("short_term.prompt", request.user_input, reason="Pipeline prompt")

        if metadata.history:
            context_manager.set("mid_term.chat_history", metadata.history, reason="Pipeline history")
        if metadata.model_params:
            context_manager.set("long_term.model_params", metadata.model_params, reason="Pipeline model params")
        if metadata.config:
            context_manager.set("long_term.config", metadata.config, reason="Pipeline config override")

    def _run_retrieval(self, context_manager: ContextManager, request: RequestCtx) -> RetrievalResult:
        log_manager.info("[RAGPipeline] Retrieving context from RAG engine")
        items = self._rag_engine.query_text(request.user_input or "", top_k=self._retrieval_top_k)
        retrieval = RetrievalResult(items=items, total=len(items))
        context_manager.set("short_term.rag_context", build_context_text(items), reason="Pipeline retrieval")
        return retrieval

    def _run_generation(self, context_manager: ContextManager) -> Generated:
        log_manager.info("[RAGPipeline] Generating response via generator endpoint")
        return self._generator.generate(context_manager)

    def _run_evaluation(self, context_manager: ContextManager) -> Evaluated:
        log_manager.info("[RAGPipeline] Evaluating generated response")
        return self._evaluator.evaluate(context_manager)

    def _persist_results(
        self,
        *,
        session_id: str,
        request: RequestCtx,
        generated: Generated,
        evaluation: Evaluated,
        metadata: PipelineMetadata,
    ) -> Persisted:
        timestamp = datetime.now(timezone.utc).isoformat()
        record_payload = {
            "session_id": session_id,
            "user_input": request.user_input,
            "answer": generated.text,
            "rating": evaluation.score,
            "feedback": evaluation.comment,
            "regeneration": metadata.regeneration or False,
            "iteration": metadata.iteration or 1,
            "timestamp": timestamp,
        }

        log_manager.info("[RAGPipeline] Persisting record via MemoryStore")
        self._memory_store.save(record_payload, iteration=record_payload["iteration"])
        try:
            self._memory_store.save_record_to_db(record_payload)
        except Exception:
            log_manager.warning("[RAGPipeline] Failed to persist to DB; continuing with file persistence only", exc_info=True)

        return Persisted(
            record_id=session_id,
            snapshot={
                "saved_at": timestamp,
                "iteration": record_payload["iteration"],
                "regeneration": record_payload["regeneration"],
            },
        )
