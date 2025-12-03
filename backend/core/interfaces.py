# path: backend/core/interfaces.py
# version: v0.1
# purpose: Define abstract interfaces for core components (RagEngine, Generator, Evaluator, MemoryStore)

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, TYPE_CHECKING, runtime_checkable

from backend.core.pipeline_models import Evaluated, Generated

if TYPE_CHECKING:
    from orchestrator.context_manager import ContextManager


@runtime_checkable
class RagEngine(Protocol):
    def query_text(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]: ...


@runtime_checkable
class Generator(Protocol):
    def generate(self, context_manager: "ContextManager") -> Generated: ...


@runtime_checkable
class Evaluator(Protocol):
    def evaluate(self, context_manager: "ContextManager") -> Evaluated: ...


@runtime_checkable
class MemoryStore(Protocol):
    def save(self, record_data: Dict[str, Any], iteration: int = 1) -> None: ...

    def save_record_to_db(self, log_data: Dict[str, Any]) -> None: ...

    def save_evaluation(self, *, session_id: str, score: int, comment: Optional[str]) -> Dict[str, Any]: ...

    def save_meta_feedback(self, payload: Dict[str, Any]) -> None: ...

    def save_auto_action(self, action: Dict[str, Any], success: Optional[bool]) -> None: ...
