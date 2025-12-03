# path: scripts/update_v0_8_1_poc_progress.py
# version: 1.0.0
# purpose: Force roadmap v0.8.1_PoC progress to 100% in DB and run doc sync.
from __future__ import annotations

import os
import subprocess
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from backend.db.connection import SessionLocal
from backend.db.models import RoadmapItem


def update_db() -> None:
    session = SessionLocal()
    try:
        item = (
            session.query(RoadmapItem)
            .filter(RoadmapItem.version == "v0.8.1_PoC")
            .first()
        )
        if not item:
            print("No v0.8.1_PoC roadmap item found.")
            return
        if item.progress != 100:
            item.progress = 100
            session.commit()
            print("Updated DB progress to 100%.")
        else:
            print("DB progress already at 100%.")
    finally:
        session.close()


def sync_docs() -> None:
    """Regenerate roadmap JSON views from DB."""
    try:
        subprocess.run(
            [sys.executable, "-m", "backend.scripts.roadmap_doc_sync"],
            check=True,
        )
        print("Regenerated docs/roadmap/*.json via roadmap_doc_sync.")
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("roadmap_doc_sync failed") from exc


def main() -> None:
    update_db()
    sync_docs()


if __name__ == "__main__":
    main()
