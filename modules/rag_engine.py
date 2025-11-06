import json
import os
import psycopg2
import datetime
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from modules.config_manager import load_environment
from modules.log_manager import log_manager

class RAGEngine:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized: # Singleton pattern
            return

        config = load_environment()
        self.qdrant_host = config.get("QDRANT_HOST", "localhost")
        self.qdrant_port = int(config.get("QDRANT_PORT", 6333))
        self.pg_host = config.get("POSTGRES_HOST", "localhost")
        self.pg_port = int(config.get("POSTGRES_PORT", 5432))
        self.pg_database = config.get("POSTGRES_DB", "world_knowledge_db")
        self.pg_user = config.get("POSTGRES_USER", "user")
        self.pg_password = config.get("POSTGRES_PASSWORD", "password")
        self.qdrant_collection_name = config.get("QDRANT_COLLECTION", "world_knowledge")

        try:
            self.qdrant_client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
            log_manager.info(f"Qdrant client initialized for {self.qdrant_host}:{self.qdrant_port}")
            self.embedding_model = SentenceTransformer(config.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))
            log_manager.info(f"Embedding model {config.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")} loaded.")
            self.pg_conn = psycopg2.connect(
                host=self.pg_host,
                port=self.pg_port,
                database=self.pg_database,
                user=self.pg_user,
                password=self.pg_password,
                client_encoding='UTF8' # Explicitly set client encoding to UTF8
            )
            log_manager.info(f"PostgreSQL connected to {self.pg_host}:{self.pg_port}/{self.pg_database}")
            self._initialized = True
        except Exception as e:
            log_manager.exception(f"RAGEngine initialization error: {e}")
            raise

    def _vectorize_query(self, query: str):
        log_manager.debug(f"Vectorizing query: {query[:50]}...")
        return self.embedding_model.encode(query).tolist()

    def _search_qdrant(self, query_vector: list):
        log_manager.debug(f"Searching Qdrant with vector (first 5 elements): {query_vector[:5]}...")
        search_result = self.qdrant_client.search(
            collection_name=self.qdrant_collection_name,
            query_vector=query_vector,
            limit=5
        )
        log_manager.debug(f"Qdrant search returned {len(search_result)} hits.")
        return [hit.id for hit in search_result]

    def _get_text_from_postgresql(self, ids: list):
        log_manager.debug(f"Fetching texts from PostgreSQL for IDs: {ids}")
        if not ids:
            log_manager.debug("No IDs provided for PostgreSQL text retrieval.")
            return []
        
        cur = self.pg_conn.cursor() # type: ignore
        id_list = ','.join(map(str, ids))
        cur.execute(f"SELECT content FROM world_knowledge WHERE id IN ({id_list}) ORDER BY id;")
        texts = [row[0] for row in cur.fetchall()]
        cur.close()
        log_manager.debug(f"Retrieved {len(texts)} texts from PostgreSQL.")
        return texts

    def get_context(self, query: str) -> str: # Reverted to get_context
        log_manager.debug(f"Getting context for query: {query}")
        context = ""
        log_data = {"query": query, "context": ""}
        try:
            query_vector = self._vectorize_query(query)
            qdrant_ids = self._search_qdrant(query_vector)
            pg_texts = self._get_text_from_postgresql(qdrant_ids)
            
            if pg_texts:
                context = "\n".join(pg_texts)
            else:
                context = "情報不足"

            log_data["context"] = context
            
            # Log query and context
            log_manager.info("RAG context retrieved.", extra=log_data)

        except Exception as e:
            context = f"RAG Engine エラー: {e}"
            log_data["context"] = context
            log_manager.exception("RAG context retrieval failed.", extra=log_data)
            raise # Re-raise the exception after logging

        return context

    def list_embeddings(self, limit: int = 50) -> list:
        log_manager.debug(f"Listing {limit} embeddings from Qdrant.")
        try:
            scroll_result, _ = self.qdrant_client.scroll(
                collection_name=self.qdrant_collection_name,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            results = []
            for hit in scroll_result:
                payload = hit.payload
                text = payload.get('answer') or payload.get('result') or payload.get('user_input') or ""
                
                results.append({
                    "id": str(hit.id),
                    "text": text,
                    "score": payload.get('rating', 0.0),
                    "source": payload.get('source', 'unknown'),
                    "created_at": payload.get('created_at', datetime.datetime.now().isoformat())
                })
            log_manager.debug(f"Listed {len(results)} embeddings.")
            return results
        except Exception as e:
            log_manager.exception(f"Error listing embeddings from Qdrant: {e}")
            return []

    def _ensure_qdrant_collection_exists(self, vector_size: int):
        from qdrant_client.http.models import Distance, VectorParams
        try:
            self.qdrant_client.get_collection(collection_name=self.qdrant_collection_name)
            log_manager.debug(f"Qdrant collection {self.qdrant_collection_name} already exists.")
        except Exception:
            log_manager.info(f"Collection {self.qdrant_collection_name} not found, creating it.")
            self.qdrant_client.recreate_collection(
                collection_name=self.qdrant_collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            log_manager.info(f"Collection {self.qdrant_collection_name} created with vector size {vector_size}.")

    def inject_samples_to_qdrant(self) -> int:
        from backend.db.connection import get_latest_samples
        
        log_manager.info("Injecting samples to Qdrant...")
        samples = get_latest_samples(limit=50)
        synced_count = 0

        if not samples:
            log_manager.info("No new samples to inject into Qdrant.")
            return 0

        points = []
        for sample in samples:
            try:
                vector = self._vectorize_query(sample.result)
                points.append({
                    "id": sample.id,
                    "vector": vector,
                    "payload": {
                        "prompt": sample.prompt,
                        "result": sample.result,
                        "created_at": sample.created_at.isoformat()
                    }
                })
            except Exception as e:
                log_manager.error(f"Error vectorizing sample {sample.id}: {e}")
                continue
        
        if points:
            try:
                self._ensure_qdrant_collection_exists(len(points[0]["vector"]))
                operation_info = self.qdrant_client.upsert(
                    collection_name=self.qdrant_collection_name,
                    wait=True,
                    points=points
                )
                synced_count = len(points)
                log_manager.info(f"Qdrant upsert operation info: {operation_info}")
            except Exception as e:
                log_manager.exception(f"Error upserting samples to Qdrant: {e}")
        
        log_manager.info(f"Finished injecting {synced_count} samples to Qdrant.")
        return synced_count

    def _upsert_single_sample_to_qdrant(self, sample_id: int, vector: list, payload: dict):
        log_manager.debug(f"Upserting single sample {sample_id} to Qdrant.")
        try:
            self._ensure_qdrant_collection_exists(len(vector))
            self.qdrant_client.upsert(
                collection_name=self.qdrant_collection_name,
                wait=True,
                points=[{
                    "id": sample_id,
                    "vector": vector,
                    "payload": payload
                }]
            )
            log_manager.debug(f"Successfully upserted sample {sample_id}.")
        except Exception as e:
            log_manager.exception(f"Error upserting single sample {sample_id} to Qdrant: {e}")

    def optimize_rag_memory(self, top_n: int = 50):
        log_manager.info("🧠 RAGメモリ最適化を開始します...")
        try:
            all_points, _ = self.qdrant_client.scroll(
                collection_name=self.qdrant_collection_name,
                limit=10000,
                with_payload=True,
                with_vectors=True
            )
            
            sorted_records = sorted(all_points, key=lambda x: x.payload.get('rating', 0.0), reverse=True)
            records_to_optimize = sorted_records[:top_n]

            for r in records_to_optimize:
                answer_text = r.payload.get('answer') or r.payload.get('result', '')
                feedback_text = r.payload.get('feedback', '')
                text = f"{answer_text}\n\n評価: {feedback_text}"
                new_vector = self._vectorize_query(text)
                self._upsert_single_sample_to_qdrant(r.id, new_vector, r.payload)
            log_manager.info(f"✅ RAGメモリの最適化が完了しました（{len(records_to_optimize)}件）")
        except Exception as e:
            log_manager.exception(f"❌ RAGメモリ最適化中にエラーが発生しました: {e}")

def register_high_score_sample(user_input: str, answer: str, rating: float, feedback: str, threshold: float = 0.7):
    log_manager.debug(f"Attempting to register high score sample with rating: {rating}")
    if rating >= threshold:
        rag = RAGEngine() # Initialize RAGEngine
        try:
            vector = rag._vectorize_query(answer)
            payload = {
                "user_input": user_input,
                "answer": answer,
                "rating": rating,
                "feedback": feedback,
                "created_at": datetime.datetime.now().isoformat()
            }
            import hashlib
            sample_id = int(hashlib.sha256(answer.encode('utf-8')).hexdigest(), 16) % (10**9)

            rag._upsert_single_sample_to_qdrant(sample_id, vector, payload)
            log_manager.info(f"✅ 高スコア応答をRAGに登録しました（スコア: {rating}）")
        except Exception as e:
            log_manager.exception(f"❌ 高スコア応答のRAG登録中にエラーが発生しました: {e}")
    else:
        log_manager.info(f"⚠️ スコアが閾値未満のためRAG登録をスキップしました（スコア: {rating}）")

def reinforce_rag_with_feedback(feedback_path="data/feedback_log.json", min_score=0.8):
    log_manager.info(f"🧠 RAG再学習を開始します... ({datetime.datetime.now()})")

    if not os.path.exists(feedback_path):
        log_manager.warning("⚠️ フィードバックログが存在しません。処理をスキップします。")
        return

    try:
        with open(feedback_path, "r", encoding="utf-8") as f:
            feedback_data = json.load(f)

        high_scores = [entry for entry in feedback_data if entry.get("rating", 0.0) >= min_score]
        if not high_scores:
            log_manager.info("📭 高評価データが見つかりません。")
            return

        rag_engine = RAGEngine()

        inserted = 0
        for entry in high_scores:
            combined_text = f"Q: {entry['user_input']}\nA: {entry['final_output']}"
            vector = rag_engine._vectorize_query(combined_text)

            import hashlib
            sample_id = int(hashlib.sha256(combined_text.encode('utf-8')).hexdigest(), 16) % (10**9)

            payload = {
                "user_input": entry["user_input"],
                "final_output": entry["final_output"],
                "rating": entry.get("rating", 0.0),
                "feedback": entry.get("feedback", ""),
                "timestamp": entry.get("timestamp", datetime.datetime.now().isoformat())
            }

            rag_engine._upsert_single_sample_to_qdrant(sample_id, vector, payload)
            inserted += 1

        log_manager.info(f"✅ RAG再学習が完了しました。登録件数: {inserted}")

    except Exception as e:
        log_manager.exception(f"❌ RAG再学習中にエラーが発生しました: {e}")
