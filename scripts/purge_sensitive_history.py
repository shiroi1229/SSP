#!/usr/bin/env python3
"""Create and optionally push a sanitized mirror of SSP history.

This tool is intentionally destructive only with --execute. It never prints the
compromised credential. It should be run from a trusted local clone that has
push access to shiroi1229/SSP after rotating the live PostgreSQL password.

Requirements:
  - git
  - git-filter-repo available as `git filter-repo`
  - authenticated Git push access to the repository

Example:
  python scripts/purge_sensitive_history.py --execute
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_FULL_NAME = "shiroi1229/SSP"
INITIAL_COMPROMISED_COMMIT = "550a05994cf521d749b155163e28d2054e519cad"
SAFE_BRANCHES = [
    "main",
    "claude/improve-completion-rate-wZ6ND",
    "codex/add-chat-answer-typing-animation",
    "codex/add-visual-page-for-domain-knowledge-overview",
    "codex/evaluate-chat-functionality",
    "codex/evaluate-chat-screen-ui",
    "codex/evaluate-orchestration",
    "codex/make-document-visibility-mandatory-during-import",
    "codex/optimize-and-integrate-chat-conversations",
    "codex/organize-inquiry-and-response-pairs",
    "codex/standardize-processing-pipeline-steps",
    "codex/visualize-kb-source-and-update-process",
    "codex-ipc8pp",
    "codex-whmhhn",
    "copilot/code-review-session",
    "feat/ssp-arch-100pt-lifespan-utc-di",
    "security/clean-root",
    "security/history-sanitization-backup",
    "security/history-sanitization-work",
    "security/history-sanitize-trigger",
    "security/old-history-hold",
    "security/sanitized-root-candidate",
]
KNOWN_MERGED_PRS_REQUIRING_GITHUB_SUPPORT = (6, 7, 8, 11, 13)


def run(cmd: list[str], *, cwd: Path | None = None, check: bool = True, capture: bool = False):
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def require_tool(command: list[str], label: str) -> None:
    try:
        run(command, check=True, capture=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(f"Required tool is unavailable: {label}") from exc


def current_origin(root: Path) -> str:
    result = run(["git", "remote", "get-url", "origin"], cwd=root, capture=True)
    value = result.stdout.strip()
    if not value:
        raise RuntimeError("Git remote 'origin' is not configured")
    return value


def ensure_expected_repo(root: Path) -> None:
    result = run(["git", "rev-parse", "--show-toplevel"], cwd=root, capture=True)
    top = Path(result.stdout.strip()).resolve()
    if top != root.resolve():
        raise RuntimeError(f"Run from the repository root: {top}")

    origin = current_origin(root)
    normalized = origin.removesuffix(".git")
    if REPO_FULL_NAME.lower() not in normalized.lower():
        raise RuntimeError(f"Refusing to operate on unexpected origin: {origin}")


def extract_compromised_password(mirror: Path) -> str:
    result = run(
        ["git", "show", f"{INITIAL_COMPROMISED_COMMIT}:.env"],
        cwd=mirror,
        capture=True,
    )
    match = re.search(r"(?m)^POSTGRES_PASSWORD=(.+)$", result.stdout)
    if not match:
        raise RuntimeError("Could not locate historical POSTGRES_PASSWORD in the known initial commit")
    secret = match.group(1).strip()
    if not secret or "\n" in secret or "\r" in secret or "\x00" in secret or "==>" in secret:
        raise RuntimeError("Historical credential has an unsupported format; aborting without changes")
    return secret


def write_secret_file(directory: Path, secret: str) -> Path:
    path = directory / "replace-text.txt"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, stat.S_IRUSR | stat.S_IWUSR)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(f"literal:{secret}==><REDACTED>\n")
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return path


def rewrite_history(mirror: Path, replace_file: Path, log_path: Path) -> None:
    cmd = [
        "git",
        "filter-repo",
        "--sensitive-data-removal",
        "--force",
        "--invert-paths",
        "--path",
        ".env",
        "--path",
        "config_snapshot.json",
        "--path",
        "logs/",
        "--path",
        "devlogs/",
        "--replace-text",
        str(replace_file),
    ]
    result = run(cmd, cwd=mirror, check=False, capture=True)
    log_path.write_text(
        (result.stdout or "") + ("\n" if result.stdout and result.stderr else "") + (result.stderr or ""),
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(f"git-filter-repo failed; diagnostic log: {log_path}")


def verify_no_secret(mirror: Path, secret_file: Path) -> None:
    refs_result = run(["git", "for-each-ref", "--format=%(refname)"], cwd=mirror, capture=True)
    refs = [line.strip() for line in refs_result.stdout.splitlines() if line.strip()]
    for ref in refs:
        grep = subprocess.run(
            ["git", "grep", "-q", "-F", "-f", str(secret_file), ref, "--", "."],
            cwd=mirror,
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if grep.returncode == 0:
            raise RuntimeError(f"Compromised credential still exists in rewritten ref: {ref}")
        if grep.returncode not in (0, 1):
            raise RuntimeError(f"Could not verify rewritten ref: {ref}")

    for ref in refs:
        tree = run(["git", "ls-tree", "-r", "--name-only", ref], cwd=mirror, capture=True)
        tracked = set(tree.stdout.splitlines())
        if ".env" in tracked or "config_snapshot.json" in tracked:
            raise RuntimeError(f"Sensitive config path still exists in rewritten ref: {ref}")


def restore_origin(mirror: Path, origin: str) -> None:
    remotes = run(["git", "remote"], cwd=mirror, capture=True).stdout.split()
    if "origin" in remotes:
        run(["git", "remote", "set-url", "origin", origin], cwd=mirror)
    else:
        run(["git", "remote", "add", "origin", origin], cwd=mirror)


def push_regular_refs(mirror: Path) -> None:
    # refs/pull/* are intentionally not pushed: GitHub makes them read-only.
    run(["git", "push", "--force", "origin", "refs/heads/*:refs/heads/*"], cwd=mirror)
    run(["git", "push", "--force", "origin", "refs/tags/*:refs/tags/*"], cwd=mirror)


def print_support_handoff(mirror: Path, log_path: Path) -> None:
    filter_dir = mirror / "filter-repo"
    if not filter_dir.exists():
        filter_dir = mirror / ".git" / "filter-repo"

    changed_refs = filter_dir / "changed-refs"
    first_changed = filter_dir / "first-changed-commits"
    orphaned_lfs = filter_dir / "orphaned_lfs_objects"

    affected_prs: list[str] = []
    if changed_refs.exists():
        for line in changed_refs.read_text(encoding="utf-8", errors="replace").splitlines():
            match = re.fullmatch(r"refs/pull/(\d+)/head", line.strip())
            if match:
                affected_prs.append(match.group(1))

    print("History rewrite and regular-ref push completed.")
    print(f"Diagnostic log: {log_path}")
    if first_changed.exists():
        print(f"GitHub Support 'First Changed Commit(s)' file: {first_changed}")
    if orphaned_lfs.exists() and orphaned_lfs.stat().st_size:
        print(f"Orphaned LFS report for GitHub Support: {orphaned_lfs}")
    if affected_prs:
        print("Affected read-only PR refs reported by git-filter-repo: " + ", ".join(sorted(set(affected_prs), key=int)))
    else:
        print(
            "Known merged PRs that may still require GitHub Support cleanup: "
            + ", ".join(f"#{n}" for n in KNOWN_MERGED_PRS_REQUIRING_GITHUB_SUPPORT)
        )
    print("Next required external action: submit the GitHub Support sensitive-data removal request.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually rewrite history and force-push branches/tags. Without this flag, only prerequisites are checked.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    try:
        require_tool(["git", "--version"], "git")
        require_tool(["git", "filter-repo", "--version"], "git-filter-repo")
        ensure_expected_repo(root)
        origin = current_origin(root)

        if not args.execute:
            print("Prerequisites passed. No history was changed.")
            print("Run with --execute only after the live PostgreSQL credential has been rotated.")
            return 0

        temp_root = Path(tempfile.mkdtemp(prefix="ssp-history-purge-"))
        mirror = temp_root / "SSP.git"
        log_path = temp_root / "git-filter-repo.log"
        replace_file: Path | None = None
        try:
            run(["git", "clone", "--mirror", origin, str(mirror)])
            compromised = extract_compromised_password(mirror)
            replace_file = write_secret_file(temp_root, compromised)
            rewrite_history(mirror, replace_file, log_path)
            verify_no_secret(mirror, replace_file)
            restore_origin(mirror, origin)
            push_regular_refs(mirror)
            print_support_handoff(mirror, log_path)
        finally:
            if replace_file:
                replace_file.unlink(missing_ok=True)
            # Keep the sanitized mirror and non-secret diagnostic files for Support.
            print(f"Sanitized mirror workspace retained at: {temp_root}")
        return 0

    except Exception as exc:
        print(f"History purge failed safely: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
