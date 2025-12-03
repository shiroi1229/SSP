from __future__ import annotations

import importlib
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, Optional

BeautifulSoup = None
detect = None
LangDetectException = Exception

try:  # pragma: no cover - optional dependency check
    bs4 = importlib.import_module("bs4")
    BeautifulSoup = getattr(bs4, "BeautifulSoup", None)
except Exception:  # pragma: no cover
    BeautifulSoup = None

try:  # pragma: no cover
    langdetect = importlib.import_module("langdetect")
    detect = getattr(langdetect, "detect", None)
    LangDetectException = getattr(langdetect, "LangDetectException", Exception)
except Exception:  # pragma: no cover
    detect = None
    LangDetectException = Exception


@dataclass
class PreprocessResult:
    text: str
    language: Optional[str]
    metadata: Dict[str, Any]


class KnowledgePreprocessor:
    """Clean raw user-provided knowledge text into a normalized form."""

    _whitespace_re = re.compile(r"\s+")

    def __init__(
        self,
        *,
        strip_html: bool = True,
        collapse_whitespace: bool = True,
        lowercase: bool = False,
        detect_language: bool = True,
    ) -> None:
        self.strip_html = strip_html
        self.collapse_whitespace = collapse_whitespace
        self.lowercase = lowercase
        self.detect_language = detect_language

    def run(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> PreprocessResult:
        if not text:
            raise ValueError("text must not be empty")
        cleaned = text
        if self.strip_html:
            cleaned = self._strip_html(cleaned)
        cleaned = unicodedata.normalize("NFKC", cleaned)
        if self.collapse_whitespace:
            cleaned = self._whitespace_re.sub(" ", cleaned)
        if self.lowercase:
            cleaned = cleaned.lower()
        cleaned = cleaned.strip()

        lang = None
        if self.detect_language and cleaned and detect:
            try:
                lang = detect(cleaned[:1000])
            except LangDetectException:  # type: ignore[arg-type]
                lang = None

        combined_meta: Dict[str, Any] = dict(metadata or {})
        combined_meta.setdefault("char_length", len(cleaned))
        if lang and "language" not in combined_meta:
            combined_meta["language"] = lang

        return PreprocessResult(text=cleaned, language=lang, metadata=combined_meta)

    def _strip_html(self, value: str) -> str:
        if not BeautifulSoup:
            return value
        soup = BeautifulSoup(value, "html.parser")
        return soup.get_text(" ", strip=True)
