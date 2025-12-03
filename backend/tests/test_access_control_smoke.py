import datetime
import os
import sys

import pytest
import types

# Stub heavy dependencies before importing project modules
sys.modules.setdefault("psycopg2", types.SimpleNamespace())
sys.modules.setdefault("psycopg2.extensions", types.SimpleNamespace(connection=object))
sys.modules.setdefault("qdrant_client", types.SimpleNamespace(QdrantClient=object))
sys.modules.setdefault("sentence_transformers", types.SimpleNamespace(SentenceTransformer=object))
sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda *args, **kwargs: None))

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from orchestrator.query_processor import QueryAccessPolicy, QueryProcessor
from modules.rag_engine import RAGEngine


class DummyQdrantClient:
    def __init__(self):
        self.upserts = []
        self.created = False

    def get_collection(self, collection_name):
        raise Exception("not found")

    def recreate_collection(self, collection_name, vectors_config):
        self.created = True

    def upsert(self, collection_name, wait, points):
        self.upserts.extend(points)


class DummyEmbeddingModel:
    def encode(self, text):
        return [0.1, 0.2, 0.3]


class DummyRAGEngine(RAGEngine):
    def __init__(self):
        # Bypass heavy initialization
        pass


def _build_ingest_ready_engine():
    engine = DummyRAGEngine.__new__(DummyRAGEngine)
    engine.qdrant_client = DummyQdrantClient()
    engine.embedding_model = DummyEmbeddingModel()
    engine.pg_conn = None
    engine.qdrant_collection_name = "test_collection"
    return engine


def test_ingest_requires_visibility():
    engine = _build_ingest_ready_engine()

    result = engine.ingest_text("hello world", visibility=None)

    assert result["ingested"] == 0
    assert engine.qdrant_client.upserts == []


def test_query_processor_filters_by_scope():
    class FakeRAG:
        def search(self, query, limit=10, offset=0):
            now = datetime.datetime.now().isoformat()
            return {
                "items": [
                    {"id": "pub", "text": "public", "visibility": "public", "source": "doc", "created_at": now, "score": 1.0},
                    {"id": "lim", "text": "limited", "visibility": "limited", "source": "doc", "created_at": now, "score": 0.9},
                    {"id": "int", "text": "internal", "visibility": "internal", "source": "doc", "created_at": now, "score": 0.8},
                ],
                "total": 3,
                "limit": limit,
                "offset": offset,
            }

    processor_public = QueryProcessor(FakeRAG(), user_scope="public")
    public_context = processor_public.build_context("query")
    assert public_context.strip() == "public"

    processor_limited = QueryProcessor(FakeRAG(), user_scope="limited")
    limited_context = processor_limited.build_context("query")
    assert "public" in limited_context
    assert "limited" in limited_context
    assert "internal" not in limited_context

    processor_internal = QueryProcessor(FakeRAG(), user_scope="internal")
    internal_context = processor_internal.build_context("query")
    assert "public" in internal_context
    assert "limited" in internal_context
    assert "internal" in internal_context


def test_allowed_levels_default_to_public():
    assert QueryAccessPolicy.allowed_levels(None) == {"public"}
    assert QueryAccessPolicy.allowed_levels("unknown") == {"public"}
