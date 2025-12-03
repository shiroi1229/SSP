from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from modules.alert_dispatcher import AlertDispatcher
from modules.kb_source_tracker import (
    collect_kb_sources,
    find_changed_files,
    load_state,
    serialize_state,
)
from modules.log_manager import log_manager

DEFAULT_STATE_PATH = Path("logs/kb_refresh_state.json")


def setup_job_logger(log_file: Path) -> logging.Logger:
    logger = logging.getLogger("kb_refresh")
    logger.setLevel(logging.INFO)
    if getattr(logger, "_kb_refresh_initialized", False):
        return logger
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)
    logger._kb_refresh_initialized = True  # type: ignore[attr-defined]
    return logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run KB refresh workflow")
    parser.add_argument(
        "--schedule",
        choices=["daily", "weekly"],
        default="daily",
        help="Schedule identifier for this run.",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=DEFAULT_STATE_PATH,
        help="Path to store incremental state for change detection.",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=Path("logs/kb_refresh.log"),
        help="Log file path for this job run.",
    )
    parser.add_argument(
        "--freshness-days",
        type=int,
        default=45,
        help="Days after which documents should be forced into re-crawl.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Detect changes and log actions without performing ingestion.",
    )
    return parser.parse_args()


def notify_failure(dispatcher: AlertDispatcher, message: str) -> None:
    result = dispatcher.dispatch_alert(message, severity="critical", target_name="default")
    if result.get("status") != "success":
        log_manager.warning(
            f"[KBRefresh] Failed to dispatch Slack alert: {result.get('reason')}."
        )
    email_result = dispatcher.dispatch_alert(message, severity="critical", target_name="email_admin")
    if email_result.get("status") != "success":
        log_manager.warning(
            f"[KBRefresh] Failed to dispatch email alert: {email_result.get('reason')}."
        )


def simulate_reingest(file_path: Path, logger: logging.Logger, dry_run: bool) -> None:
    action = "Simulated re-ingest" if dry_run else "Re-ingesting"
    logger.info(f"{action}: {file_path}")


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    job_logger = setup_job_logger(args.log_file)
    dispatcher = AlertDispatcher()

    try:
        state = load_state(args.state_file)
        last_commit = state.get("last_commit")
        job_logger.info(
            f"Starting KB refresh job (schedule={args.schedule}, last_commit={last_commit})."
        )
        changed_files = find_changed_files(repo_root, last_commit)
        inventory = collect_kb_sources([repo_root / "data", repo_root / "modules"], repo_root)
        recrawl_candidates = [
            src.path
            for src in inventory.stale_sources(args.freshness_days)
        ]
        to_process = set(changed_files + [repo_root / p for p in recrawl_candidates])
        if not to_process:
            job_logger.info("No KB changes detected; nothing to re-ingest.")
        for file_path in sorted(to_process):
            simulate_reingest(file_path.relative_to(repo_root), job_logger, args.dry_run)
        current_commit = (
            state.get("last_commit")
            if args.dry_run
            else _get_current_commit(repo_root)
        )
        new_state = {
            "last_run": datetime.utcnow().isoformat() + "Z",
            "last_commit": current_commit,
            "schedule": args.schedule,
            "processed": [str(path.relative_to(repo_root)) for path in to_process],
        }
        serialize_state(args.state_file, new_state)
        job_logger.info(
            f"KB refresh completed (processed={len(to_process)}, dry_run={args.dry_run})."
        )
    except Exception as exc:  # noqa: BLE001
        message = f"KB refresh job failed: {exc}"
        job_logger.exception(message)
        notify_failure(dispatcher, message)
        raise


def _get_current_commit(repo_root: Path) -> str:
    commit = _run_git_command(["rev-parse", "HEAD"], repo_root)
    return commit or ""


def _run_git_command(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        log_manager.warning(
            f"[KBRefresh] Git command failed ({' '.join(args)}): {result.stderr.strip()}"
        )
        return ""
    return result.stdout.strip()


if __name__ == "__main__":
    main()
