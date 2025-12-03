# path: backend/core/services/pipeline_adapters.py
# version: v0.1
# purpose: Default adapters that bridge legacy module implementations to the new Protocol interfaces

from __future__ import annotations

import datetime
from typing import Any, Dict, Optional

from backend.core.interfaces import Evaluator, Generator, MemoryStore
from backend.core.pipeline_models import Evaluated, Generated
from orchestrator.context_manager import ContextManager
from modules.evaluator import evaluate_output
from modules.generator import generate_response
from modules.log_manager import log_manager
from modules.memory_store import MemoryStore as LegacyMemoryStore


class ContextGeneratorAdapter(Generator):
    """Adapter that runs the legacy generator module against a ContextManager."""

    def __init__(self) -> None:
        self._impl = generate_response

    def generate(self, context_manager: ContextManager) -> Generated:
        self._impl(context_manager)
        output = context_manager.get("mid_term.generated_output")
        if not output:
            raise RuntimeError("Generator did not produce output")
        return Generated(text=output, meta={"source": "modules.generator"})


class ContextEvaluatorAdapter(Evaluator):
    """Adapter that captures evaluator results from the ContextManager."""

    def __init__(self) -> None:
        self._impl = evaluate_output

    def evaluate(self, context_manager: ContextManager) -> Evaluated:
        self._impl(context_manager)
        score = context_manager.get("mid_term.evaluation_score")
        feedback = context_manager.get("mid_term.evaluation_feedback")
        return Evaluated(score=score, comment=feedback)


class FileMemoryStoreAdapter(MemoryStore):
    """Wraps modules.memory_store.MemoryStore to satisfy the MemoryStore Protocol."""

    def __init__(self, store: Optional[LegacyMemoryStore] = None) -> None:
        self._store = store or LegacyMemoryStore()

    def save(self, record_data: Dict[str, Any], iteration: int = 1) -> None:
        self._store.save(record_data, iteration=iteration)

    def save_record_to_db(self, log_data: Dict[str, Any]) -> None:
        self._store.save_record_to_db(log_data)

    def save_evaluation(self, *, session_id: str, score: int, comment: Optional[str]) -> Dict[str, Any]:
        record = {
            "session_id": session_id,
            "user_input": "",
            "answer": "",
            "rating": score,
            "feedback": comment,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        self._store.save(record)
        return {
            "session_id": session_id,
            "updated_evaluation_score": score,
            "updated_evaluation_comment": comment,
        }

    def save_meta_feedback(self, payload: Dict[str, Any]) -> None:
        log_manager.info("[FileMemoryStoreAdapter] meta feedback persistence is a no-op in file mode", extra={"payload": payload})

    def save_auto_action(self, action: Dict[str, Any], success: Optional[bool]) -> None:
        log_manager.info(
            "[FileMemoryStoreAdapter] auto action logging is not supported; ignoring entry",
            extra={"action": action, "success": success},
        )
