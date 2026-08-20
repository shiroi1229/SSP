# path: orchestrator/learner.py
# version: v2.4

import os
import json
import datetime
import uuid
from typing import Any
from modules.embedding_utils import get_embedding
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, Range
from modules.log_manager import log_manager
from orchestrator.context_manager import ContextManager

COLLECTION_NAME = "ssp_dev_knowledge"

class Learner:
    """Manages the learning process, recording optimization outcomes and providing weighted experience."""

    def __init__(self, context_manager: ContextManager, qdrant_client: QdrantClient):
        self.context_manager = context_manager
        self.qdrant_client = qdrant_client
        log_manager.info("[Learner] Initialized with v2.4 components.")

        # Ensure Qdrant collection exists
        try:
            if not self.qdrant_client.collection_exists(collection_name=COLLECTION_NAME):
                # Assuming a default vector size for now, will be dynamic later
                vector_size = 384 # Example size for all-MiniLM-L6-v2
                self.qdrant_client.recreate_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config={"size": vector_size, "distance": "Cosine"}
                )
                log_manager.info(f"[Learner] Qdrant collection '{COLLECTION_NAME}' created.")
        except Exception as e:
            log_manager.error(f"[Learner] Failed to connect or create Qdrant collection: {e}")

    def record_optimization_outcome(self, outcome: dict, reason: str = "Optimization cycle outcome"):
        """
        Records the outcome of an optimization cycle to Qdrant and updates the learning map.
        Outcome should include 'text' for embedding, 'improvement_score' (0-1), and other metadata.
        """
        if "text" not in outcome or "improvement_score" not in outcome:
            log_manager.error("[Learner] Outcome must contain 'text' and 'improvement_score'.")
            return

        text_to_embed = outcome["text"]
        improvement_score = outcome["improvement_score"]
        metadata = outcome.get("metadata", {})
        metadata["improvement_score"] = improvement_score
        metadata["timestamp"] = datetime.datetime.now().isoformat()

        embedding = get_embedding(text_to_embed)
        point_id = str(uuid.uuid4()) # Generate a unique ID for each point

        try:
            self.qdrant_client.upsert(
                collection_name=COLLECTION_NAME,
                points=[
                    PointStruct(id=point_id, vector=embedding, payload=metadata)
                ]
            )
            log_manager.info(f"[Learner] Optimization outcome recorded to Qdrant (ID: {point_id}, Score: {improvement_score}).")
            self.context_manager.set("long_term.learning_map", {point_id: outcome}, reason=reason)
        except Exception as e:
            log_manager.error(f"[Learner] Failed to upsert to Qdrant: {e}")

    def get_weighted_experience(self, query_text: str, limit: int = 5) -> list:
        """
        Queries Qdrant for similar cases and returns them weighted by improvement_score.
        """
        try:
            query_embedding = get_embedding(query_text)
            
            search_result = self.qdrant_client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_embedding,
                limit=limit,
                query_filter=Filter(
                    must=[
                        FieldCondition(key="improvement_score", range=Range(gte=0.5)) # Only consider reasonably good experiences
                    ]
                )
            )

            weighted_experiences = []
            for hit in search_result:
                payload = hit.payload
                # Weight by similarity and improvement score
                weight = hit.score * payload.get("improvement_score", 0.0)
                weighted_experiences.append({"payload": payload, "weight": weight, "similarity": hit.score})
            
            weighted_experiences.sort(key=lambda x: x["weight"], reverse=True)
            log_manager.info(f"[Learner] Retrieved {len(weighted_experiences)} weighted experiences for query.")
            return weighted_experiences
        except Exception as e:
            log_manager.error(f"[Learner] Failed to search Qdrant: {e}")
            return []

    def update_learning_map(self, key: str, value: Any, reason: str = "Learning map update"):
        """
        Updates a specific entry in the long-term learning map.
        """
        current_map = self.context_manager.get("long_term.learning_map") or {}
        current_map[key] = value
        self.context_manager.set("long_term.learning_map", current_map, reason=reason)

# Example usage (for testing, typically run via Orchestrator)
if __name__ == "__main__":
    log_manager.info("Learner standalone execution not fully supported in v2.4. Run via Orchestrator.")
    # Placeholder for testing
    # from orchestrator.context_manager import ContextManager
    # cm = ContextManager()
    # q_client = QdrantClient(url=os.getenv("QDRANT_URL", "http://127.0.0.1:6333"))
    # learner = Learner(cm, q_client)
    # 
    # # Example: Record a successful optimization
    # learner.record_optimization_outcome(
    #     outcome={
    #         "text": "Improved response generation by adjusting temperature to 0.7",
    #         "improvement_score": 0.85,
    #         "metadata": {"module": "generator", "change": "temperature_adjust"}
    #     },
    #     reason="Successful generator optimization"
    # )
    # 
    # # Example: Get weighted experience
    # experiences = learner.get_weighted_experience("how to improve response quality")
    # log_manager.info(f"Weighted Experiences: {experiences}")