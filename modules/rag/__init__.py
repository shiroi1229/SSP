# path: modules/rag/__init__.py
# version: v0.2
# purpose: Package init for RAG submodules (retrieval, rerank, formatting, engine)

from .retrieval import RagRetriever  # noqa: F401
from .engine import CompositeRagEngine  # re-export for convenience
