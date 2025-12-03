import json
import os
import uuid
import psycopg2
import datetime
from collections import Counter
from threading import Lock
from typing import Iterable, Optional
from pathlib import Path
from psycopg2.extensions import connection as PGConnection
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from modules.config_manager import load_environment
from modules.log_manager import log_manager
from modules.knowledge_pipeline import KnowledgePipeline, KnowledgeChunk

_resource_lock = Lock()
_shared_qdrant_clients: dict[tuple[str, int], QdrantClient] = {}
_shared_embedding_models: dict[str, SentenceTransformer] = {}
_shared_pg_connections: dict[tuple[str, int, str, str, str], PGConnection] = {}


def _get_shared_qdrant_client(host: str, port: int) -> QdrantClient:
    key = (host, port)
    client = _shared_qdrant_clients.get(key)
    if client:
        return client
    with _resource_lock:
        client = _shared_qdrant_clients.get(key)
        if client:
            return client
        client = QdrantClient(host=host, port=port)
        _shared_qdrant_clients[key] = client
        return client


def _get_shared_embedding_model(model_name: str) -> SentenceTransformer:
    model = _shared_embedding_models.get(model_name)
    if model:
        return model
    with _resource_lock:
        model = _shared_embedding_models.get(model_name)
        if model:
            return model
        model = SentenceTransformer(model_name)
        _shared_embedding_models[model_name] = model
        return model


def _get_shared_pg_connection(host: str, port: int, database: str, user: str, password: str):
    key = (host, port, database, user, password)
    conn = _shared_pg_connections.get(key)
    if conn and getattr(conn, "closed", 1) == 0:
        return conn
    with _resource_lock:
        conn = _shared_pg_connections.get(key)
        if conn and getattr(conn, "closed", 1) == 0:
            return conn
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            client_encoding='UTF8'
        )
        _shared_pg_connections[key] = conn
        return conn

class RAGEngine:
    def __init__(self, collection_name: str = None):
        config = load_environment()
        self.qdrant_host = config.get("QDRANT_HOST", "localhost")
        self.qdrant_port = int(config.get("QDRANT_PORT", 6333))
        self.pg_host = config.get("POSTGRES_HOST", "localhost")
        self.pg_port = int(config.get("POSTGRES_PORT", 5432))
        self.pg_database = config.get("POSTGRES_DB", "ssp_memory")
        self.pg_user = config.get("POSTGRES_USER", "ssp_admin")
        self.pg_password = config.get("POSTGRES_PASSWORD", "Mizuho0824")
        self.qdrant_collection_name = collection_name or config.get("QDRANT_COLLECTION", "world_knowledge")

        self.qdrant_client = None
        self.embedding_model = None
        self.pg_conn = None
        self.pipeline = KnowledgePipeline()

        try:
            self.qdrant_client = _get_shared_qdrant_client(self.qdrant_host, self.qdrant_port)
            log_manager.info(f"Qdrant client ready for {self.qdrant_host}:{self.qdrant_port} (shared).")

            embedding_name = config.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            self.embedding_model = _get_shared_embedding_model(embedding_name)
            log_manager.info(f"Embedding model {embedding_name} loaded (shared).")

            self.pg_conn = _get_shared_pg_connection(
                self.pg_host,
                self.pg_port,
                self.pg_database,
                self.pg_user,
                self.pg_password
            )
            log_manager.info(f"PostgreSQL connected to {self.pg_host}:{self.pg_port}/{self.pg_database} (shared).")
        except Exception as e:
            log_manager.exception(f"RAGEngine initialization error: {e}. RAG will be unavailable.")
            self.qdrant_client = None
            self.embedding_model = None
            self.pg_conn = None

    def _ensure_pg_connection(self):
        if self.pg_conn and getattr(self.pg_conn, "closed", 1) == 0:
            return self.pg_conn
        try:
            self.pg_conn = _get_shared_pg_connection(
                self.pg_host,
                self.pg_port,
                self.pg_database,
                self.pg_user,
                self.pg_password
            )
            log_manager.debug("PostgreSQL connection refreshed for RAGEngine instance.")
        except Exception as e:
            log_manager.exception(f"Failed to refresh PostgreSQL connection: {e}")
            self.pg_conn = None
        return self.pg_conn

    def _vectorize_query(self, query: str):
        if not self.embedding_model:
            return []
        log_manager.debug(f"Vectorizing query: {query[:50]}...")
        return self.embedding_model.encode(query).tolist()

    def _upsert_chunk(self, chunk: KnowledgeChunk) -> Optional[str]:
        try:
            vector = self._vectorize_query(chunk.text)
            if not vector:
                log_manager.warning(
                    f"Skipping chunk {chunk.metadata.get('chunk_index')} due to failed vectorization."
                )
                return None
            self._ensure_qdrant_collection_exists(len(vector))
            self.qdrant_client.upsert(
                collection_name=self.qdrant_collection_name,
                wait=True,
                points=[{
                    "id": chunk.id,
                    "vector": vector,
                    "payload": {"text": chunk.text, **chunk.metadata},
                }]
            )
            return chunk.id
        except Exception as exc:
            log_manager.exception(
                f"Failed to upsert chunk {chunk.id} into collection {self.qdrant_collection_name}: {exc}"
            )
            return None

    def upsert_text(self, doc_id: str, text: str, metadata: dict = None):
        """Vectorizes and upserts a single text document into the collection."""
        if not self.qdrant_client:
            log_manager.error("Cannot upsert text: RAGEngine is not available.")
            return
            
        log_manager.debug(f"Upserting text to collection '{self.qdrant_collection_name}' with ID: {doc_id}")
        try:
            vector = self._vectorize_query(text)
            if not vector:
                log_manager.error("Cannot upsert text: Vectorization failed.")
                return

            payload = {"text": text}
            if metadata:
                payload.update(metadata)
            
            self._ensure_qdrant_collection_exists(len(vector))
            
            self.qdrant_client.upsert(
                collection_name=self.qdrant_collection_name,
                wait=True,
                points=[{
                    "id": doc_id,
                    "vector": vector,
                    "payload": payload
                }]
            )
            log_manager.info(f"Successfully upserted text with ID {doc_id} to collection '{self.qdrant_collection_name}'.")
        except Exception as e:
            log_manager.exception(f"Error upserting text with ID {doc_id}: {e}")

    def ingest_text(
        self,
        text: str | Iterable[str] | os.PathLike,
        *,
        source: str = "manual_paste",
        treat_as_chat: bool = False,
        chunk_size: int = 800,
        overlap: int = 120,
        title: Optional[str] = None,
        tags: Optional[list[str]] = None,
        permission_label: str = "public",
    ) -> dict:
        output_path = self.pipeline.make_output_path(source)
        ingested_chunks: list[dict] = []
        written = 0
        vectorization_enabled = bool(self.qdrant_client and self.embedding_model)

        if isinstance(text, str) and not text.strip():
            log_manager.warning("Cannot ingest text: provided content is empty.")
            return {"ingested": 0, "chunks": [], "jsonl_path": str(output_path)}

        try:
            chunk_iterator = self.pipeline.iter_chunks(
                text,
                source=source,
                treat_as_chat=treat_as_chat,
                chunk_size=chunk_size,
                overlap=overlap,
                title=title,
                tags=tags,
                permission_label=permission_label,
            )

            output_path.parent.mkdir(parents=True, exist_ok=True)
            futures: dict = {}
            with output_path.open("w", encoding="utf-8") as jsonl_file:
                if vectorization_enabled:
                    from concurrent.futures import ThreadPoolExecutor, as_completed
                    with ThreadPoolExecutor(max_workers=self.pipeline.max_workers) as executor:
                        for chunk in chunk_iterator:
                            written += 1
                            jsonl_file.write(json.dumps(chunk.to_jsonl(), ensure_ascii=False) + "\n")
                            futures[executor.submit(self._upsert_chunk, chunk)] = chunk
                        for future in as_completed(futures):
                            chunk = futures[future]
                            chunk_id = future.result()
                            if chunk_id:
                                ingested_chunks.append({"id": chunk_id, "text": chunk.text})
                else:
                    for chunk in chunk_iterator:
                        written += 1
                        jsonl_file.write(json.dumps(chunk.to_jsonl(), ensure_ascii=False) + "\n")

            if not written:
                log_manager.warning("No segments produced during ingestion.")
        except Exception as exc:
            log_manager.exception(f"Failed to ingest text: {exc}")

        if not vectorization_enabled and written:
            log_manager.error(
                f"Embeddings were not generated because RAGEngine is unavailable. JSONL saved to {output_path}."
            )

        log_manager.info(
            f"Ingested {len(ingested_chunks)}/{written} chunks into collection "
            f"'{self.qdrant_collection_name}' (source={source}, chat={treat_as_chat})"
        )

        return {"ingested": len(ingested_chunks), "chunks": ingested_chunks, "jsonl_path": str(output_path)}

    def ingest_file(self, file_path: os.PathLike, **kwargs) -> dict:
        resolved = Path(file_path)
        source = kwargs.pop("source", resolved.stem)
        return self.ingest_text(
            resolved,
            source=source,
            **kwargs,
        )

    def query_text(self, query: str, top_k: int = 3) -> list[dict]:
        """Queries the collection for similar texts and returns their payloads."""
        if not self.qdrant_client:
            log_manager.error("Cannot query text: RAGEngine is not available.")
            return []

        log_manager.debug(f"Querying collection '{self.qdrant_collection_name}' with query: {query[:50]}...")
        try:
            query_vector = self._vectorize_query(query)
            if not query_vector:
                log_manager.error("Cannot query text: Vectorization failed.")
                return []

            search_result = self.qdrant_client.search(
                collection_name=self.qdrant_collection_name,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True
            )
            results = [hit.payload for hit in search_result]
            log_manager.debug(f"Query returned {len(results)} results from collection '{self.qdrant_collection_name}'.")
            return results
        except Exception as e:
            log_manager.exception(f"Error querying collection '{self.qdrant_collection_name}': {e}")
            return []

    def _search_qdrant(self, query_vector: list):
        if not self.qdrant_client:
            return []
        log_manager.debug(f"Searching Qdrant with vector (first 5 elements): {query_vector[:5]}...")
        search_result = self.qdrant_client.search(
            collection_name=self.qdrant_collection_name,
            query_vector=query_vector,
            limit=5
        )
        log_manager.debug(f"Qdrant search returned {len(search_result)} hits.")
        return [hit.id for hit in search_result]

    def _get_text_from_postgresql(self, ids: list):
        conn = self._ensure_pg_connection()
        if not conn:
            log_manager.error("PostgreSQL connection is unavailable for text retrieval.")
            return []
        log_manager.debug(f"Fetching texts from PostgreSQL for IDs: {ids}")
        if not ids:
            log_manager.debug("No IDs provided for PostgreSQL text retrieval.")
            return []

        cur = conn.cursor()
        try:
            id_list = ','.join(map(str, ids))
            cur.execute(f"SELECT content FROM world_knowledge WHERE id IN ({id_list}) ORDER BY id;")
            texts = [row[0] for row in cur.fetchall()]
            log_manager.debug(f"Retrieved {len(texts)} texts from PostgreSQL.")
            return texts
        finally:
            cur.close()

    def _format_hit(self, hit, score_hint=None):
        payload = getattr(hit, "payload", {}) or {}
        text = payload.get("answer") or payload.get("result") or payload.get("text") or payload.get("user_input") or ""
        created_at = (
            payload.get("created_at")
            or payload.get("ingested_at")
            or payload.get("timestamp")
            or datetime.datetime.now().isoformat()
        )
        source = payload.get("source") or payload.get("module") or payload.get("source_name") or "unknown"
        score = score_hint if score_hint is not None else payload.get("rating") or payload.get("score") or 0.0
        permission_label = payload.get("permission_label") or payload.get("permission")
        return {
            "id": str(getattr(hit, "id", payload.get("id", ""))),
            "text": text,
            "score": float(score),
            "source": source,
            "created_at": created_at,
            "permission_label": permission_label,
        }

    def _parse_datetime(self, value: str):
        try:
            return datetime.datetime.fromisoformat(value)
        except Exception:
            try:
                return datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
            except Exception:
                return datetime.datetime.min

    def _build_score_summary(self, scores: list[float]):
        cleaned = [score for score in scores if isinstance(score, (int, float))]
        if not cleaned:
            return {"min": None, "max": None, "avg": None, "p95": None}
        cleaned.sort()
        avg = sum(cleaned) / len(cleaned)
        p95_index = min(max(int(len(cleaned) * 0.95) - 1, 0), len(cleaned) - 1)
        return {
            "min": cleaned[0],
            "max": cleaned[-1],
            "avg": avg,
            "p95": cleaned[p95_index],
        }

    def _apply_sort(self, entries: list[dict], order_by: str, descending: bool):
        reverse = descending
        if order_by == "score":
            entries.sort(key=lambda entry: entry["score"], reverse=reverse)
        else:
            entries.sort(
                key=lambda entry: self._parse_datetime(entry["created_at"]),
                reverse=reverse,
            )
        return entries

    def _collect_source_counts(self, entries: list[dict]):
        return dict(Counter(entry["source"] for entry in entries))

    def get_context(self, query: str) -> str: # Reverted to get_context
        if not self.qdrant_client or not self.embedding_model or not self._ensure_pg_connection():
            log_manager.error("Cannot get context: RAGEngine is not available.")
            return "RAG Engine is currently unavailable."

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
            # Do not re-raise, return the error message in the context

        return context

    def list_embeddings(
        self,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at",
        descending: bool = True,
    ) -> dict:
        if not self.qdrant_client:
            log_manager.error("Cannot list embeddings: RAGEngine is not available.")
            return {
                "items": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "source_counts": {},
                "score_summary": self._build_score_summary([]),
            }
        log_manager.debug(f"Listing embeddings from Qdrant (limit={limit}, offset={offset}).")

        total_count = 0
        try:
            total_count = self.qdrant_client.count(collection_name=self.qdrant_collection_name).count
        except Exception as e:
            log_manager.warning(f"Failed to count collection '{self.qdrant_collection_name}': {e}")

        try:
            scroll_result, _ = self.qdrant_client.scroll(
                collection_name=self.qdrant_collection_name,
                limit=limit,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            entries = []
            for hit in scroll_result:
                try:
                    entries.append(self._format_hit(hit))
                except Exception as err:
                    log_manager.warning(f"Skipping hit due to formatting error: {err}")
            entries = self._apply_sort(entries, order_by if order_by in {"score", "created_at"} else "created_at", descending)
            source_counts = self._collect_source_counts(entries)
            score_summary = self._build_score_summary([entry["score"] for entry in entries])
            log_manager.debug(f"Listed {len(entries)} embeddings (total={total_count}).")
            return {
                "items": entries,
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "source_counts": source_counts,
                "score_summary": score_summary,
            }
        except Exception as e:
            log_manager.exception(f"Error listing embeddings from Qdrant: {e}")
            return {
                "items": [],
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "source_counts": {},
                "score_summary": self._build_score_summary([]),
            }

    def search(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        order_by: str = "score",
        descending: bool = True,
    ) -> dict:
        if not self.qdrant_client or not self.embedding_model:
            log_manager.error("Cannot search embeddings: RAGEngine is not available.")
            return {
                "items": [],
                "total": 0,
                "source_counts": {},
                "score_summary": self._build_score_summary([]),
                "query": query,
                "limit": limit,
                "offset": offset,
            }

    def get_by_id(self, entry_id: str):
        if not self.qdrant_client:
            log_manager.error("Cannot retrieve entry: RAGEngine is not available.")
            return None
        try:
            point = self.qdrant_client.retrieve(
                collection_name=self.qdrant_collection_name,
                point_id=entry_id,
                with_payload=True,
            )
            if not point or not getattr(point, "payload", None):
                return None
            return self._format_hit(point)
        except Exception as exc:
            log_manager.exception(f"Failed to fetch entry {entry_id}: {exc}")
            return None

        log_manager.debug(f"Searching RAG for query='{query}' (limit={limit}, offset={offset}).")
        query_vector = self._vectorize_query(query)
        if not query_vector:
            return {
                "items": [],
                "total": 0,
                "source_counts": {},
                "score_summary": self._build_score_summary([]),
                "query": query,
                "limit": limit,
                "offset": offset,
            }

        try:
            search_limit = max(limit + offset, 1)
            search_result = self.qdrant_client.search(
                collection_name=self.qdrant_collection_name,
                query_vector=query_vector,
                limit=search_limit,
                with_payload=True,
            )
            entries = []
            for hit in search_result:
                try:
                    entries.append(self._format_hit(hit, score_hint=getattr(hit, "score", None)))
                except Exception as err:
                    log_manager.warning(f"Skipping hit during search formatting: {err}")
            entries = self._apply_sort(
                entries,
                order_by if order_by in {"score", "created_at"} else "score",
                descending,
            )
            total_hits = len(entries)
            paged = entries[offset: offset + limit]
            score_summary = self._build_score_summary([entry["score"] for entry in entries])
            return {
                "items": paged,
                "total": total_hits,
                "limit": limit,
                "offset": offset,
                "query": query,
                "source_counts": self._collect_source_counts(entries),
                "score_summary": score_summary,
            }
        except Exception as e:
            log_manager.exception(f"Error running search for '{query}': {e}")
            return {
                "items": [],
                "total": 0,
                "source_counts": {},
                "score_summary": self._build_score_summary([]),
                "query": query,
                "limit": limit,
                "offset": offset,
            }

    def _ensure_qdrant_collection_exists(self, vector_size: int):
        if not self.qdrant_client:
            return
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
        if not self.qdrant_client:
            log_manager.error("Cannot inject samples: RAGEngine is not available.")
            return 0
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
                if not vector: continue
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
        if not self.qdrant_client:
            return
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
        if not self.qdrant_client:
            log_manager.error("Cannot optimize memory: RAGEngine is not available.")
            return
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
                if new_vector:
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
