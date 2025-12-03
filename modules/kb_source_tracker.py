from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Optional

from modules.log_manager import log_manager

KB_EXTENSIONS = {".json", ".yaml", ".yml", ".md", ".txt", ".py", ".sql", ".csv"}
EXCLUDE_DIR_NAMES = {"__pycache__", "audio_outputs", "node_modules", "logs", ".git"}


def _run_git_command(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        log_manager.warning(
            f"[KBTracker] Git command failed ({' '.join(args)}): {result.stderr.strip()}"
        )
        return ""
    return result.stdout.strip()


def _git_last_commit_info(path: Path, repo_root: Path) -> tuple[Optional[datetime], str, str]:
    git_output = _run_git_command(
        ["log", "-1", "--format=%cs||%cn||%H", "--", str(path)], repo_root
    )
    if not git_output:
        return None, "Untracked", ""
    date_str, author, commit_hash = git_output.split("||")
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        dt = None
    return dt, author or "Unknown", commit_hash


def _git_commit_count_since(path: Path, days: int, repo_root: Path) -> int:
    since = f"--since={days}.days"
    output = _run_git_command(
        ["log", since, "--format=%H", "--", str(path)], repo_root
    )
    return len(output.splitlines()) if output else 0


def infer_update_frequency(commits_30d: int, commits_90d: int) -> str:
    if commits_30d >= 12:
        return "Daily"
    if commits_30d >= 4:
        return "Weekly"
    if commits_90d >= 4:
        return "Bi-weekly"
    if commits_90d >= 1:
        return "Monthly"
    return "Rare"


def infer_priority(last_updated: Optional[datetime], frequency: str, category: str) -> str:
    if not last_updated:
        return "High"
    age_days = (datetime.now() - last_updated).days
    if age_days > 90:
        return "High"
    if category == "data" and age_days > 45:
        return "High"
    if frequency in {"Daily", "Weekly"}:
        return "High" if category == "modules" else "Medium"
    if age_days > 30:
        return "Medium"
    return "Low"


def should_recrawl(last_updated: Optional[datetime], freshness_days: int) -> bool:
    if not last_updated:
        return True
    return (datetime.now() - last_updated) > timedelta(days=freshness_days)


@dataclass
class KBSourceRecord:
    path: Path
    category: str
    last_updated: Optional[datetime]
    responsible: str
    update_frequency: str
    priority: str
    commit_hash: str = ""
    commits_30d: int = 0
    commits_90d: int = 0
    notes: str = ""

    def to_markdown_row(self) -> str:
        last_updated_str = self.last_updated.strftime("%Y-%m-%d") if self.last_updated else "N/A"
        return (
            f"| `{self.path}` | {self.category} | {self.update_frequency} | "
            f"{last_updated_str} | {self.responsible} | {self.priority} | {self.notes} |"
        )


@dataclass
class KBInventory:
    sources: List[KBSourceRecord] = field(default_factory=list)

    def stale_sources(self, freshness_days: int) -> List[KBSourceRecord]:
        return [
            src
            for src in self.sources
            if should_recrawl(src.last_updated, freshness_days)
        ]

    def to_markdown(self, freshness_days: int) -> str:
        header = (
            "# KB Source Inventory\n\n"
            "This report catalogs knowledge base sources under `data/` and `modules/`, "
            "including freshness, responsibility, and re-crawl priority.\n\n"
            "| Source | Category | Update Frequency | Last Updated | Responsible | Priority | Notes |\n"
            "| --- | --- | --- | --- | --- | --- | --- |\n"
        )
        rows = "\n".join(src.to_markdown_row() for src in self.sources)
        recrawl = self.stale_sources(freshness_days)
        recrawl_section = [
            "\n## Re-crawl Candidates\n",
        ]
        if not recrawl:
            recrawl_section.append("All sources are within the freshness window.\n")
        else:
            recrawl_section.append(
                "The following sources are older than the freshness threshold "
                f"({freshness_days} days) or have no recorded updates.\n"
            )
            recrawl_section.append("\n| Source | Last Updated | Responsible | Reason |\n| --- | --- | --- | --- |\n")
            for src in recrawl:
                last_updated = (
                    src.last_updated.strftime("%Y-%m-%d") if src.last_updated else "N/A"
                )
                reason = "Outdated" if src.last_updated else "No history"
                recrawl_section.append(
                    f"| `{src.path}` | {last_updated} | {src.responsible} | {reason} |"
                )
        return header + rows + "\n" + "\n".join(recrawl_section)


def collect_kb_sources(base_paths: Iterable[Path], repo_root: Path) -> KBInventory:
    sources: List[KBSourceRecord] = []
    for base in base_paths:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_dir():
                continue
            if path.suffix not in KB_EXTENSIONS:
                continue
            if any(part in EXCLUDE_DIR_NAMES for part in path.parts):
                continue
            last_updated, author, commit_hash = _git_last_commit_info(path, repo_root)
            commits_30d = _git_commit_count_since(path, 30, repo_root)
            commits_90d = _git_commit_count_since(path, 90, repo_root)
            frequency = infer_update_frequency(commits_30d, commits_90d)
            category = "data" if base.name == "data" else "modules"
            priority = infer_priority(last_updated, frequency, category)
            notes = "High-churn" if commits_30d > 8 else ""
            record = KBSourceRecord(
                path=path.relative_to(repo_root),
                category=category,
                last_updated=last_updated,
                responsible=author,
                update_frequency=frequency,
                priority=priority,
                commit_hash=commit_hash,
                commits_30d=commits_30d,
                commits_90d=commits_90d,
                notes=notes,
            )
            sources.append(record)
    sources.sort(key=lambda r: (r.category, r.path.as_posix()))
    return KBInventory(sources=sources)


def serialize_state(state_path: Path, payload: dict) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_state(state_path: Path) -> dict:
    if not state_path.exists():
        return {}
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        log_manager.warning(f"[KBTracker] Failed to parse state file at {state_path}, starting fresh.")
        return {}


def find_changed_files(repo_root: Path, since_commit: Optional[str]) -> list[Path]:
    if since_commit:
        output = _run_git_command(
            ["diff", "--name-only", f"{since_commit}..HEAD", "--", "data", "modules"],
            repo_root,
        )
    else:
        output = _run_git_command(["ls-files", "data", "modules"], repo_root)

    changed: list[Path] = []
    for line in output.splitlines():
        candidate = repo_root / Path(line.strip())
        if not line.strip():
            continue
        if any(part in EXCLUDE_DIR_NAMES for part in candidate.parts):
            continue
        if candidate.suffix and candidate.suffix not in KB_EXTENSIONS:
            continue
        changed.append(candidate)
    return changed
