"""
Utility script to refresh the roadmap dump from PostgreSQL and print a
prefix-level progress summary with an explicit Awareness focus section.

Usage:
    python scripts/roadmap_status.py

Optional flags:
    --skip-dump      Skips the DB export step and only prints the summary.
    --focus PREFIX   Focus on a prefix other than the default 'A'.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List

REPO_ROOT = Path(__file__).resolve().parents[1]
ROADMAP_DUMP = REPO_ROOT / "roadmap_dump.json"


def run_dump() -> None:
    """Invoke dump_roadmap_to_file.py with the current interpreter."""
    script_path = REPO_ROOT / "dump_roadmap_to_file.py"
    cmd = [sys.executable, str(script_path)]
    print(f"\n$ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=REPO_ROOT, check=True)


def load_dump() -> List[Dict]:
    if not ROADMAP_DUMP.exists():
        raise SystemExit(
            "roadmap_dump.json が見つかりません。まず dump_roadmap_to_file.py を実行してください。"
        )
    with ROADMAP_DUMP.open(encoding="utf-8") as fh:
        return json.load(fh)


def summarize_by_prefix(items: Iterable[Dict]) -> List[Dict]:
    summary = defaultdict(lambda: {"count": 0, "completed": 0, "in_progress": 0, "not_started": 0})
    for item in items:
        version = item.get("version", "")
        prefix = version.split("-")[0] if "-" in version else version
        progress = item.get("progress") or 0
        summary[prefix]["count"] += 1
        if progress >= 100:
            summary[prefix]["completed"] += 1
        elif progress > 0:
            summary[prefix]["in_progress"] += 1
        else:
            summary[prefix]["not_started"] += 1

    ordered = sorted(summary.items(), key=lambda kv: kv[0])
    return [{"prefix": prefix, **stats} for prefix, stats in ordered]


def format_bar(stats: Dict) -> str:
    total = stats["count"]
    if total == 0:
        return "-"
    completed = stats["completed"] / total
    in_progress = stats["in_progress"] / total
    segments = []
    if completed:
        segments.append(f"✅ {completed:>5.0%}")
    if in_progress:
        segments.append(f"⏳ {in_progress:>5.0%}")
    if stats["not_started"]:
        not_started = stats["not_started"] / total
        segments.append(f"⚪ {not_started:>5.0%}")
    return " | ".join(segments) or "0%"


def print_summary(summary: List[Dict]) -> None:
    print("\n=== Roadmap Prefix Summary ===")
    header = f"{'Prefix':<10} {'Total':>5} {'Done':>5} {'Active':>6} {'Queued':>6}  Breakdown"
    print(header)
    print("-" * len(header))
    for entry in summary:
        line = (
            f"{entry['prefix']:<10} "
            f"{entry['count']:>5} "
            f"{entry['completed']:>5} "
            f"{entry['in_progress']:>6} "
            f"{entry['not_started']:>6}  "
            f"{format_bar(entry)}"
        )
        print(line)


def print_focus(items: List[Dict], focus_prefix: str) -> None:
    focus_items = [
        i
        for i in items
        if (i.get("version") or "").startswith(focus_prefix + "-") and (i.get("progress") or 0) < 100
    ]
    if not focus_items:
        print(f"\n{focus_prefix} 系の未完了項目はありません ✅")
        return

    print(f"\n=== {focus_prefix} prefix - Attention Needed ===")
    for item in sorted(focus_items, key=lambda i: i.get("version", "")):
        progress = item.get("progress")
        progress_str = f"{progress}%" if progress is not None else "N/A"
        status = item.get("status", "未設定")
        print(f"- {item.get('version'):<8} {progress_str:>6} {status} :: {item.get('codename')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Dump roadmap data and print aggregated status.")
    parser.add_argument("--skip-dump", action="store_true", help="Skip DB dump and use the existing JSON.")
    parser.add_argument("--focus", default="A", help="Prefix to highlight (default: A).")
    args = parser.parse_args()

    if not args.skip_dump:
        run_dump()

    items = load_dump()
    summary = summarize_by_prefix(items)
    print_summary(summary)
    print_focus(items, args.focus)


if __name__ == "__main__":
    main()
