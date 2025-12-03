from __future__ import annotations

import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

# Provide lightweight stubs for optional heavy dependencies to keep tests isolated.
sys.modules.setdefault("psycopg2", types.SimpleNamespace(connect=lambda *_, **__: None))
sys.modules.setdefault("psycopg2.extensions", types.SimpleNamespace(connection=None))
sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda *_, **__: None))


class _Distance:
    COSINE = "cosine"


class _VectorParams:
    def __init__(self, size: int, distance: str):
        self.size = size
        self.distance = distance


sys.modules.setdefault("qdrant_client", types.SimpleNamespace(QdrantClient=object))
sys.modules.setdefault(
    "qdrant_client.http.models",
    types.SimpleNamespace(Distance=_Distance, VectorParams=_VectorParams),
)
sys.modules.setdefault("sentence_transformers", types.SimpleNamespace(SentenceTransformer=object))

from modules.knowledge_pipeline import KnowledgePipeline
from modules.rag_engine import RAGEngine


class _FakeEmbedding:
    class _VectorResult(list):
        def tolist(self):
            return list(self)

    def encode(self, text: str):
        return self._VectorResult([float(i) for i in range(3)])


class _FakeQdrant:
    def __init__(self):
        self.points: list[dict] = []

    def upsert(self, collection_name: str, wait: bool, points: list[dict]):
        self.points.extend(points)


def test_pipeline_cleans_and_splits(tmp_path: Path):
    pipeline = KnowledgePipeline(output_dir=tmp_path)
    raw = """
    <h1>Title</h1>

    Paragraph one with&nbsp;space.

    ## Topic
    Second paragraph with <b>HTML</b> tags.
    """

    chunks = list(
        pipeline.iter_chunks(
            raw,
            source="unit",
            chunk_size=120,
            overlap=0,
            title="Doc",
            tags=["demo"],
            permission_label="internal",
        )
    )

    assert chunks
    assert all("<" not in chunk.text and ">" not in chunk.text for chunk in chunks)
    assert "## Topic" in chunks[-1].text
    assert chunks[0].metadata["permission_label"] == "internal"
    assert chunks[0].metadata["source"] == "unit"
    assert chunks[0].metadata["type"] == "document"


def test_rag_engine_streams_to_jsonl(tmp_path: Path):
    rag = RAGEngine.__new__(RAGEngine)
    rag.qdrant_client = _FakeQdrant()
    rag.embedding_model = _FakeEmbedding()
    rag.qdrant_collection_name = "test"
    rag.pipeline = KnowledgePipeline(output_dir=tmp_path)
    rag._ensure_qdrant_collection_exists = lambda _size: None

    result = RAGEngine.ingest_text(
        rag,
        "Speaker: Hello\nMore details here.\n\nNew topic starts",
        source="integration",
        chunk_size=64,
        overlap=0,
        permission_label="restricted",
    )

    jsonl_path = Path(result["jsonl_path"])
    assert jsonl_path.exists()
    saved_records = [json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines()]
    assert saved_records
    assert all(record["metadata"]["permission_label"] == "restricted" for record in saved_records)

    assert result["ingested"] == len(rag.qdrant_client.points)
    assert rag.qdrant_client.points
    assert all(point["payload"].get("text") for point in rag.qdrant_client.points)
