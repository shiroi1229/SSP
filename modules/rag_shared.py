# path: modules/rag_shared.py
# version: v0.1
# purpose: Provide shared resource helpers for RAG (Qdrant, embeddings, PostgreSQL)

from __future__ import annotations

from threading import Lock
from typing import Dict, Tuple

import psycopg2
from psycopg2.extensions import connection as PGConnection
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer


class SharedRAGResources:
    """Thread-safe cache for expensive RAG dependencies."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._qdrant_clients: Dict[Tuple[str, int], QdrantClient] = {}
        self._embedding_models: Dict[str, SentenceTransformer] = {}
        self._pg_connections: Dict[Tuple[str, int, str, str, str], PGConnection] = {}

    def get_qdrant_client(self, host: str, port: int) -> QdrantClient:
        key = (host, port)
        client = self._qdrant_clients.get(key)
        if client:
            return client
        with self._lock:
            client = self._qdrant_clients.get(key)
            if client:
                return client
            client = QdrantClient(host=host, port=port)
            self._qdrant_clients[key] = client
            return client

    def get_embedding_model(self, model_name: str) -> SentenceTransformer:
        model = self._embedding_models.get(model_name)
        if model:
            return model
        with self._lock:
            model = self._embedding_models.get(model_name)
            if model:
                return model
            model = SentenceTransformer(model_name)
            self._embedding_models[model_name] = model
            return model

    def get_pg_connection(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
    ) -> PGConnection:
        key = (host, port, database, user, password)
        conn = self._pg_connections.get(key)
        if conn and getattr(conn, "closed", 1) == 0:
            return conn
        with self._lock:
            conn = self._pg_connections.get(key)
            if conn and getattr(conn, "closed", 1) == 0:
                return conn
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                client_encoding="UTF8",
            )
            self._pg_connections[key] = conn
            return conn


GLOBAL_RAG_RESOURCES = SharedRAGResources()
