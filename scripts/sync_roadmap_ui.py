#!/usr/bin/env python
"""
Utility to keep UI-related roadmap entries in sync with implemented components.

Usage:
  python sync_roadmap_ui.py --version UI-v3.5 --progress 40 \
      --features frontend/components/dashboard/MetaAwarenessFeed.tsx \
      --details "Meta-Awareness timeline linked with Shared Mind console."

The script updates the RoadmapItem row matching the supplied version, adjusting
progress, keyFeatures, and development_details when specified.
"""
from argparse import ArgumentParser
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.db.connection import SessionLocal
from backend.db.models import RoadmapItem
from backend.scripts.roadmap_doc_sync import sync_roadmap_documents


def parse_args() -> ArgumentParser:
    parser = ArgumentParser(description="Sync UI roadmap metadata with file changes.")
    parser.add_argument("--version", required=True, help="Roadmap version string (e.g., UI-v3.5).")
    parser.add_argument("--progress", type=int, help="New progress percentage.")
    parser.add_argument(
        "--features",
        nargs="+",
        help="List of changed feature paths to set as keyFeatures.",
    )
    parser.add_argument("--details", help="New development_details text.")
    return parser


def update_roadmap_item(version: str, progress: int | None, features: list[str] | None, details: str | None):
    session = SessionLocal()
    try:
        item = session.query(RoadmapItem).filter(RoadmapItem.version == version).first()
        if not item:
            raise ValueError(f"Roadmap item {version} not found.")

        if progress is not None:
            item.progress = max(0, min(100, progress))
        if features:
            item.keyFeatures = features
        if details:
            item.development_details = details

        session.commit()
        print(f"[sync_roadmap_ui] Updated {version}")
        sync_roadmap_documents()
    except Exception as exc:
        session.rollback()
        print(f"[sync_roadmap_ui] Failed to update {version}: {exc}")
    finally:
        session.close()


def main():
    parser = parse_args()
    args = parser.parse_args()
    update_roadmap_item(args.version, args.progress, args.features, args.details)


if __name__ == "__main__":
    main()
