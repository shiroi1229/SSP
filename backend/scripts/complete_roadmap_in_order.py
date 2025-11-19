from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import List

from backend.db.connection import SessionLocal
from backend.db.models import RoadmapItem as DBRoadmapItem
from backend.db.schemas import RoadmapItem
from backend.utils.roadmap_utils import parse_version_sort_key
from backend.scripts.roadmap_doc_sync import sync_roadmap_documents


@dataclass
class UpdateSpec:
    id: int
    version: str
    target_progress: int = 100
    target_status: str = "✅"


def sorted_roadmap_items(session) -> List[DBRoadmapItem]:
    items = session.query(DBRoadmapItem).all()
    return sorted(items, key=lambda item: parse_version_sort_key(item.version))


def main():
    parser = argparse.ArgumentParser(description="Complete roadmap entries in version order.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log the updates without persisting them.",
    )
    args = parser.parse_args()

    session = SessionLocal()
    try:
        ordered = sorted_roadmap_items(session)
        print("Roadmap completion order:")
        updates = []
        for item in ordered:
            if (item.progress or 0) >= 100 and item.status == "✅":
                print(f" - {item.version}: already complete")
                continue
            updates.append(UpdateSpec(id=item.id, version=item.version))
            print(f" - {item.version}: scheduling completion")

        if args.dry_run or not updates:
            return

        for spec in updates:
            db_item = session.query(DBRoadmapItem).filter(DBRoadmapItem.id == spec.id).first()
            if not db_item:
                continue
            db_item.progress = spec.target_progress
            db_item.status = spec.target_status
            session.add(db_item)
        session.commit()
        sync_roadmap_documents()
        print("Applied sequential completion and synced docs.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
