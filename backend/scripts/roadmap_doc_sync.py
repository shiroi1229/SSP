from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from backend.db.connection import SessionLocal
from backend.db.models import RoadmapItem as DBRoadmapItem
from backend.db.schemas import RoadmapItem as RoadmapItemSchema
from backend.utils.roadmap_utils import categorize_version, parse_version_sort_key
from modules.log_manager import log_manager


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOC_DIR = PROJECT_ROOT / "docs" / "roadmap"
DOC_PATHS = [
    DOC_DIR / "system_roadmap.json",
    DOC_DIR / "system_roadmap_extended.json",
]
DUMP_PATH = PROJECT_ROOT / "roadmap_dump.json"


def _serialize_item(item: DBRoadmapItem) -> Dict:
    pydantic_item = RoadmapItemSchema.model_validate(item)
    data = pydantic_item.model_dump(by_alias=True, exclude_none=False)
    data.pop("id", None)
    return data


def _ensure_doc_dirs() -> None:
    DOC_DIR.mkdir(parents=True, exist_ok=True)


def _build_category_payload(serialized: List[Dict]) -> Dict[str, List[Dict]]:
    categories = {name: [] for name in ("backend", "frontend", "robustness", "Awareness_Engine")}
    for record in serialized:
        category = categorize_version(record.get("version"))
        categories.setdefault(category, []).append(record)
    return categories


def _write_file(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sync_roadmap_documents() -> bool:
    session = SessionLocal()
    try:
        items = session.query(DBRoadmapItem).all()
        items.sort(key=lambda item: parse_version_sort_key(item.version))
        serialized = [_serialize_item(item) for item in items]
    except Exception as exc:
        log_manager.exception(f"Failed to query roadmap items for doc sync: {exc}")
        return False
    finally:
        session.close()

    try:
        _ensure_doc_dirs()
        category_payload = _build_category_payload(serialized)
        _write_file(DUMP_PATH, serialized)
        for doc_path in DOC_PATHS:
            _write_file(doc_path, category_payload)
        log_manager.info("Roadmap documentation synced from database.")
        return True
    except Exception as exc:
        log_manager.exception(f"Failed to write roadmap documentation: {exc}")
        return False


if __name__ == "__main__":
    success = sync_roadmap_documents()
    exit(0 if success else 1)
