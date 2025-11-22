"""
Add a roadmap item 'UI-v0.2' to the database using the RoadmapItem model.

Usage:
  python backend/scripts/add_roadmap_ui_v0_2.py

This script opens a DB session via SessionLocal and upserts a roadmap item by
`key`/`slug` (adjust the lookup field if your model uses a different unique
identifier). It is intentionally conservative: it only inserts if not exists,
or updates a small set of fields if present.

After running this, run:
  python -m backend.scripts.roadmap_doc_sync
to regenerate `docs/roadmap/*.json`.
"""
from typing import Optional
import sys
import os

# Ensure project root (one level above `backend`) is on sys.path so `backend` is importable
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(project_root))

from backend.db.connection import SessionLocal
from backend.db.models import RoadmapItem

DATA = {
    "version": "ui-v0.2",
    "codename": "UI v0.2",
    "title": "UI v0.2 — 評価UI改善と評価パネルの非占有化",
    "status": "planned",
    "progress": 0,
    "description": "チャット評価パネルが送信直後にチャットを占有する問題を解消する。折りたたみ式表示とモーダル化の検討を含む。",
    "development_details": "短期: 評価パネルを折りたたみ式（'評価を表示'ボタン）に変更。中期: 評価をモーダル化してチャット流を阻害しないUXにする。",
}


def upsert_roadmap_item(session, version: str, data: dict) -> Optional[RoadmapItem]:
    # Use `version` as the unique identifier for roadmap items
    existing = session.query(RoadmapItem).filter(RoadmapItem.version == version).one_or_none()
    if existing:
        print(f"Found existing roadmap item with version={version}, updating fields.")
        # Update a conservative set of fields
        existing.codename = data.get('codename', existing.codename)
        existing.goal = data.get('title', existing.goal)
        existing.status = data.get('status', existing.status)
        existing.progress = data.get('progress', existing.progress)
        existing.description = data.get('description', existing.description)
        existing.development_details = data.get('development_details', getattr(existing, 'development_details', None))
        session.add(existing)
        session.commit()
        return existing

    print(f"Creating new roadmap item with version={version}.")
    item = RoadmapItem(
        version=version,
        codename=data.get('codename'),
        goal=data.get('title'),
        status=data.get('status'),
        progress=data.get('progress', 0),
        description=data.get('description'),
        development_details=data.get('development_details'),
    )
    session.add(item)
    session.commit()
    return item


def main():
    session = SessionLocal()
    try:
        item = upsert_roadmap_item(session, DATA['version'], DATA)
        if item:
            print("✅ Roadmap item upserted:", item)
        else:
            print("⚠️ No item created/updated.")
    except Exception as e:
        print("Error while upserting roadmap item:", e)
    finally:
        session.close()


if __name__ == '__main__':
    main()
