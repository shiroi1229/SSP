# path: modules/stage_memory.py
# version: UI-v1.2
"""
Integrates past stage performances into the AI's long-term memory (RAG + Context).
"""

import os
import sys
import json
from datetime import datetime

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.log_manager import log_manager
from modules.rag_engine import RAGEngine
from orchestrator.context_manager import ContextManager


class StageMemoryManager:
    """Aggregates and embeds stage logs into long-term RAG memory."""

    def __init__(self, log_dir="logs/stage_runs"):
        self.log_dir = log_dir
        self.rag = RAGEngine(collection_name="stage_memories")
        self.context = ContextManager(history_path="logs/context_history.json")
        os.makedirs(self.log_dir, exist_ok=True)

    def sync_stage_memories(self):
        """Scan all stage logs and embed new ones into RAG memory."""
        try:
            log_files = sorted([f for f in os.listdir(self.log_dir) if f.endswith(".json")])
        except FileNotFoundError:
            log_manager.warning(f"[StageMemory] Log directory not found: {self.log_dir}")
            return
            
        new_count = 0
        for log_file in log_files:
            try:
                log_path = os.path.join(self.log_dir, log_file)
                with open(log_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                summary = self._summarize_stage(data)
                vector_id = f"stage_{data['run_id']}"
                
                # Here we assume the RAG engine can handle upserting based on a unique ID
                self.rag.upsert_text(vector_id, summary, metadata=data)
                new_count += 1
            except Exception as e:
                log_manager.error(f"[StageMemory] Failed to process log file {log_file}: {e}", exc_info=True)
                continue

        log_manager.info(f"[StageMemory] Synced {new_count} stage memories into RAG.")
        self.context.set(
            "long_term.stage_memory.last_sync",
            datetime.now().isoformat(),
            reason=f"Synced {new_count} stage runs"
        )

    def _summarize_stage(self, data: dict) -> str:
        """Condenses stage data into a textual summary for RAG storage."""
        timeline = data.get("timeline", [])
        if not timeline:
            return f"Empty Stage Run {data.get('run_id', 'unknown')}"
            
        characters = {e.get("character") for e in timeline}
        emotions = [e.get("emotion", "neutral") for e in timeline]
        avg_duration = sum([e.get("duration", 0) for e in timeline]) / len(timeline)

        return (
            f"Stage Run {data.get('run_id', 'unknown')} with {len(characters)} characters. "
            f"Dominant emotions: {', '.join(set(emotions))}. "
            f"Average segment length: {avg_duration:.2f}s. "
            f"Final state: stable. Successful playback."
        )

    def query_stage_knowledge(self, query: str) -> str:
        """Retrieve related past stage data via semantic search."""
        results = self.rag.query_text(query, top_k=3)
        return "\n".join([r.get("text", "") for r in results])
