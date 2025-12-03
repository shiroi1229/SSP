from __future__ import annotations

from dataclasses import dataclass
from typing import List

try:  # pragma: no cover - optional dependency check
    import tiktoken  # type: ignore
except ImportError:  # pragma: no cover
    tiktoken = None  # type: ignore


@dataclass
class Chunk:
    index: int
    text: str
    start: int
    end: int


class TokenChunker:
    """Split text into token-aware chunks suitable for embeddings."""

    def __init__(
        self,
        *,
        max_tokens: int = 512,
        overlap_tokens: int = 64,
        encoding_name: str = "cl100k_base",
    ) -> None:
        if max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.encoding_name = encoding_name
        self.encoding = self._load_encoding()

    def chunk(self, text: str) -> List[Chunk]:
        if not text:
            return []
        if not self.encoding:
            return self._fallback_chunk(text)

        tokens = self.encoding.encode(text)
        chunks: List[Chunk] = []
        if not tokens:
            return []

        start_token = 0
        idx = 0
        while start_token < len(tokens):
            end_token = min(start_token + self.max_tokens, len(tokens))
            token_slice = tokens[start_token:end_token]
            chunk_text = self.encoding.decode(token_slice)
            chunk_start = start_token
            chunk_end = end_token
            chunks.append(Chunk(index=idx, text=chunk_text, start=chunk_start, end=chunk_end))
            idx += 1
            if self.overlap_tokens > 0 and end_token < len(tokens):
                start_token = max(0, end_token - self.overlap_tokens)
            else:
                start_token = end_token
        return chunks

    def _load_encoding(self):
        if not tiktoken:
            return None
        try:
            return tiktoken.get_encoding(self.encoding_name)
        except Exception:  # pragma: no cover
            return None

    def _fallback_chunk(self, text: str) -> List[Chunk]:
        window = self.max_tokens * 4
        if window <= 0:
            window = 512
        chunks: List[Chunk] = []
        idx = 0
        for start in range(0, len(text), window):
            end = min(start + window, len(text))
            chunks.append(Chunk(index=idx, text=text[start:end], start=start, end=end))
            idx += 1
        return chunks
