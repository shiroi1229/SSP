from __future__ import annotations

import datetime as _dt
import html
import io
import json
import os
import re
import unicodedata
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator


@dataclass
class KnowledgeChunk:
    id: str
    text: str
    metadata: dict

    def to_jsonl(self) -> dict:
        return {"id": self.id, "text": self.text, "metadata": self.metadata}


class KnowledgePipeline:
    """Pipeline for cleaning, splitting, and persisting knowledge documents."""

    _topic_pattern = re.compile(r"^(?:#{1,6}\s+|\d+\.\s+|[-\*+]\s+)")
    _speaker_pattern = re.compile(r"^\s*[^:：]+[:：]\s*")

    def __init__(self, output_dir: str | Path = "data/processed", max_workers: int | None = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        cpu_count = os.cpu_count() or 2
        self.max_workers = max_workers or max(2, min(8, cpu_count))

    def _iter_lines(self, source: str | Path | Iterable[str]) -> Iterator[str]:
        if isinstance(source, (str, Path)) and Path(source).is_file():
            with Path(source).open("r", encoding="utf-8", errors="ignore") as handle:
                for line in handle:
                    yield line
        elif isinstance(source, str):
            for line in io.StringIO(source):
                yield line
        else:
            yield from source

    def _strip_html(self, text: str) -> str:
        text = re.sub(r"<script.*?>.*?</script>", " ", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<style.*?>.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        return text

    def _normalize_text(self, text: str) -> str:
        unescaped = html.unescape(text)
        collapsed = self._strip_html(unescaped)
        normalized = unicodedata.normalize("NFKC", collapsed)
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip()

    def _iter_paragraphs(self, source: str | Path | Iterable[str]) -> Iterator[str]:
        buffer: list[str] = []
        for raw_line in self._iter_lines(source):
            normalized = self._normalize_text(raw_line)
            if not normalized:
                if buffer:
                    yield " ".join(buffer).strip()
                    buffer = []
                continue
            buffer.append(normalized)
        if buffer:
            yield " ".join(buffer).strip()

    def _iter_chat_turns(self, source: str | Path | Iterable[str]) -> Iterator[str]:
        buffer: list[str] = []
        for raw_line in self._iter_lines(source):
            normalized = self._normalize_text(raw_line)
            if not normalized:
                continue
            if self._speaker_pattern.match(normalized):
                if buffer:
                    yield " ".join(buffer).strip()
                    buffer = []
                yield normalized
            else:
                buffer.append(normalized)
        if buffer:
            yield " ".join(buffer).strip()

    def _iter_topics(self, paragraphs: Iterable[str]) -> Iterator[str]:
        current: list[str] = []
        for paragraph in paragraphs:
            if self._topic_pattern.match(paragraph):
                if current:
                    yield " ".join(current).strip()
                current = [paragraph]
            else:
                current.append(paragraph)
        if current:
            yield " ".join(current).strip()

    def _chunk_segments(self, segments: Iterable[str], chunk_size: int, overlap: int) -> Iterator[str]:
        current = ""
        for segment in segments:
            if not segment:
                continue
            segment = segment.strip()
            while segment:
                available = chunk_size - len(current) - (1 if current else 0)
                if available <= 0:
                    if current:
                        yield current.strip()
                    overlap_tail = current[-overlap:] if overlap > 0 else ""
                    current = overlap_tail
                    available = chunk_size - len(current) - (1 if current else 0)
                if len(segment) <= available:
                    current = f"{current}\n{segment}".strip() if current else segment
                    segment = ""
                else:
                    head = segment[:available]
                    segment = segment[available:]
                    current = f"{current}\n{head}".strip() if current else head
                    yield current.strip()
                    overlap_tail = current[-overlap:] if overlap > 0 else ""
                    current = overlap_tail
        if current.strip():
            yield current.strip()

    def iter_chunks(
        self,
        text_source: str | Path | Iterable[str],
        *,
        source: str,
        treat_as_chat: bool = False,
        chunk_size: int = 800,
        overlap: int = 120,
        title: str | None = None,
        tags: list[str] | None = None,
        permission_label: str = "public",
    ) -> Iterator[KnowledgeChunk]:
        overlap = max(0, min(overlap, chunk_size // 2))
        chunk_size = max(200, chunk_size)
        created_at = _dt.datetime.utcnow().isoformat()
        base_id = uuid.uuid4().hex
        base_metadata = {
            "source": source,
            "ingested_at": created_at,
            "title": title,
            "tags": tags or [],
            "type": "chat" if treat_as_chat else "document",
            "permission_label": permission_label,
        }

        segments = (
            self._iter_chat_turns(text_source)
            if treat_as_chat
            else self._iter_topics(self._iter_paragraphs(text_source))
        )

        for idx, chunk_text in enumerate(self._chunk_segments(segments, chunk_size, overlap)):
            metadata = {
                **base_metadata,
                "chunk_index": idx,
                "text_length": len(chunk_text),
            }
            yield KnowledgeChunk(
                id=f"{base_id}-{idx}",
                text=chunk_text,
                metadata=metadata,
            )

    def make_output_path(self, source: str) -> Path:
        timestamp = _dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        safe_source = re.sub(r"[^a-zA-Z0-9_\-]+", "_", source) or "unknown"
        filename = f"processed_{safe_source}_{timestamp}.jsonl"
        return self.output_dir / filename

    def write_jsonl(self, chunks: Iterable[KnowledgeChunk], output_path: Path) -> None:
        with output_path.open("w", encoding="utf-8") as handle:
            for chunk in chunks:
                handle.write(json.dumps(chunk.to_jsonl(), ensure_ascii=False) + "\n")
