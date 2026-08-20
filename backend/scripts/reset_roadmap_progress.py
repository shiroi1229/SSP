from __future__ import annotations

from backend.db.connection import SessionLocal
from backend.db.models import RoadmapItem
from backend.scripts.roadmap_doc_sync import sync_roadmap_documents

def main():
    session = SessionLocal()
    try:
        items = session.query(RoadmapItem).all()
        for item in items:
            item.progress = 0
            item.status = "⚪"
            session.add(item)
        session.commit()
        sync_roadmap_documents()
        print("Reset all roadmap progress to 0% and synced docs.")
    finally:
        session.close()

if __name__ == "__main__":
    main()
