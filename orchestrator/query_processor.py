"""
Query processing layer with visibility-aware filtering.
"""
from typing import Iterable, List, Set

from modules.log_manager import log_manager
from modules.rag_engine import RAGEngine


class QueryAccessPolicy:
    """Determines which visibility levels a user can access."""

    VISIBILITY_MAP = {
        "public": {"public"},
        "limited": {"public", "limited"},
        "internal": {"public", "limited", "internal"},
    }

    @classmethod
    def allowed_levels(cls, user_scope: str | None) -> Set[str]:
        normalized = (user_scope or "public").lower()
        return cls.VISIBILITY_MAP.get(normalized, cls.VISIBILITY_MAP["public"])

    @classmethod
    def filter_results(cls, results: Iterable[dict], user_scope: str | None) -> List[dict]:
        allowed = cls.allowed_levels(user_scope)
        filtered: List[dict] = []
        for result in results:
            visibility = str(result.get("visibility") or "public").lower()
            if visibility in allowed:
                filtered.append(result)
            else:
                required = ", ".join(sorted(allowed))
                log_manager.info(
                    f"Skipping result {result.get('id', 'unknown')} due to insufficient visibility (required one of {required})."
                )
        return filtered


class QueryProcessor:
    """Executes RAG searches while enforcing user visibility constraints."""

    def __init__(self, rag_engine: RAGEngine, user_scope: str | None = None):
        self.rag_engine = rag_engine
        self.user_scope = user_scope or "public"

    def search(self, query: str, limit: int = 10, offset: int = 0) -> dict:
        result = self.rag_engine.search(query, limit=limit, offset=offset)
        filtered_items = QueryAccessPolicy.filter_results(result.get("items", []), self.user_scope)
        skipped = max(len(result.get("items", [])) - len(filtered_items), 0)
        if skipped:
            log_manager.info(f"Filtered out {skipped} results due to visibility rules.")
        return {**result, "items": filtered_items, "filtered_out": skipped}

    def build_context(self, query: str, limit: int = 5) -> str:
        search_result = self.search(query, limit=limit)
        items = search_result.get("items", [])
        if not items:
            log_manager.warning("No accessible context found for query '%s'", query)
            return ""
        return "\n".join(filter(None, (item.get("text", "") for item in items)))
