from pathlib import Path
import argparse
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from modules.kb_source_tracker import collect_kb_sources
from modules.log_manager import log_manager


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate KB source inventory report")
    parser.add_argument(
        "--report-path",
        type=Path,
        default=Path("reports/kb_inventory.md"),
        help="Path to save the generated Markdown report.",
    )
    parser.add_argument(
        "--freshness-days",
        type=int,
        default=45,
        help="Days after which a document is considered stale for re-crawl.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    inventory = collect_kb_sources(
        base_paths=[repo_root / "data", repo_root / "modules"],
        repo_root=repo_root,
    )
    report_markdown = inventory.to_markdown(args.freshness_days)
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text(report_markdown, encoding="utf-8")
    log_manager.info(
        f"[KBInventory] Report written to {args.report_path} covering {len(inventory.sources)} sources."
    )


if __name__ == "__main__":
    main()
