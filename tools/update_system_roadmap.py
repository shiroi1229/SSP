"""
Sync docs/roadmap/system_roadmap*.json with the latest roadmap_dump.json.

Usage:
    python tools/update_system_roadmap.py [--dump path]

The script reads roadmap_dump.json (produced by dump_roadmap_to_file.py) and:
1. Buckets items by prefix into backend/frontend/robustness/Awareness_Engine.
2. Writes docs/roadmap/system_roadmap_extended.json with the full dataset.
3. Writes docs/roadmap/system_roadmap.json with only v0.x–v2.5 entries (legacy view).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
DUMP_PATH = REPO_ROOT / "roadmap_dump.json"
EXTENDED_PATH = REPO_ROOT / "docs" / "roadmap" / "system_roadmap_extended.json"
LEGACY_PATH = REPO_ROOT / "docs" / "roadmap" / "system_roadmap.json"


def load_dump(path: Path) -> List[Dict]:
    if not path.exists():
        raise SystemExit(f"{path} が見つかりません。先に dump_roadmap_to_file.py を実行してください。")
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def categorize(items: List[Dict]) -> Dict[str, List[Dict]]:
    buckets: Dict[str, List[Dict]] = {
        "backend": [],
        "frontend": [],
        "robustness": [],
        "Awareness_Engine": [],
    }
    for item in items:
        version = item.get("version", "")
        if version.startswith("UI-"):
            buckets["frontend"].append(item)
        elif version.startswith("R-"):
            buckets["robustness"].append(item)
        elif version.startswith("A-"):
            buckets["Awareness_Engine"].append(item)
        else:
            buckets["backend"].append(item)
    return buckets


def write_json(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_version_number(version: str) -> float | None:
    if not version.startswith("v"):
        return None
    try:
        body = version[1:]
        return float(body.replace("v", "")) if "v" in body else float(body)
    except ValueError:
        return None


def build_legacy_view(categorized: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
    legacy = {"backend": [], "frontend": [], "robustness": []}
    for key in ("backend", "frontend", "robustness"):
        collected: List[Dict] = []
        for item in categorized.get(key, []):
            version = item.get("version", "")
            number = parse_version_number(version if version.startswith("v") else version.split("-", 1)[-1])
            if number is not None and number <= 2.5:
                collected.append(item)
        legacy[key] = collected
    return legacy


def main() -> None:
    parser = argparse.ArgumentParser(description="Update roadmap docs from roadmap_dump.json")
    parser.add_argument("--dump", type=Path, default=DUMP_PATH, help="Path to roadmap_dump.json")
    args = parser.parse_args()

    items = load_dump(args.dump)
    categorized = categorize(items)
    write_json(EXTENDED_PATH, categorized)
    legacy = build_legacy_view(categorized)
    write_json(LEGACY_PATH, legacy)

    print(f"Updated {EXTENDED_PATH} and {LEGACY_PATH} from {args.dump}")


if __name__ == "__main__":
    main()
