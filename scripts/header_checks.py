# path: scripts/header_checks.py
# version: v0.1
# purpose: Validate 3-line headers and UTF-8 encoding across Python files

from __future__ import annotations

import argparse
import codecs
import sys
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TOKENS = ("# path:", "# version:", "# purpose:")
SKIP_PARTS = {"__pycache__", ".git", "node_modules", ".next"}
SKIP_DIRS = {"data", "logs", "docs", "frontend/.next"}


def _iter_targets(patterns: Sequence[str] | None) -> Iterable[Path]:
    if patterns:
        for pattern in patterns:
            for entry in ROOT.glob(pattern):
                if entry.is_file() and entry.suffix == ".py":
                    yield entry
                elif entry.is_dir():
                    yield from entry.rglob("*.py")
    else:
        yield from ROOT.rglob("*.py")


def _should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if parts & SKIP_PARTS:
        return True
    if any(seg in path.as_posix() for seg in SKIP_DIRS):
        return True
    return False


def _read_text(path: Path) -> tuple[str, bool]:
    raw = path.read_bytes()
    has_bom = raw.startswith(codecs.BOM_UTF8)
    text = raw.decode("utf-8-sig" if has_bom else "utf-8")
    return text, has_bom


def _check_header(path: Path, text: str, bom: bool) -> list[str]:
    rel = path.relative_to(ROOT).as_posix()
    issues: list[str] = []
    lines = text.splitlines()
    if bom:
        issues.append("contains UTF-8 BOM")
    if len(lines) < 3:
        issues.append("missing 3-line header")
        return issues
    for token, line in zip(EXPECTED_TOKENS, lines[:3]):
        if token not in line:
            issues.append(f"header missing '{token}'")
    expected_path = f"# path: {rel}"
    if lines[0].strip() != expected_path:
        issues.append(f"path header mismatch (expected '{expected_path}')")
    if not lines[1].split(":", 1)[-1].strip():
        issues.append("version header empty")
    if not lines[2].split(":", 1)[-1].strip():
        issues.append("purpose header empty")
    return issues


def run_checks(patterns: Sequence[str] | None) -> list[str]:
    problems: list[str] = []
    for file_path in _iter_targets(patterns):
        if file_path.suffix != ".py" or _should_skip(file_path):
            continue
        try:
            text, has_bom = _read_text(file_path)
        except Exception as exc:  # pragma: no cover - surfaced in CLI
            problems.append(f"{file_path}: unable to read ({exc})")
            continue
        issues = _check_header(file_path, text, has_bom)
        problems.extend(f"{file_path}: {issue}" for issue in issues)
    return problems


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate SSP header conventions")
    parser.add_argument(
        "--paths",
        nargs="*",
        help="Optional glob patterns or directories to limit scope",
    )
    args = parser.parse_args(argv)

    problems = run_checks(args.paths)
    if problems:
        print("[header_checks] issues detected:")
        print("\n".join(sorted(problems)))
        return 1
    print("[header_checks] all files compliant")
    return 0


if __name__ == "__main__":
    sys.exit(main())
