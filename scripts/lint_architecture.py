# path: scripts/lint_architecture.py
# version: v0.1
# purpose: SSP規範の静的検査（禁止import/3行ヘッダ/行数上限）

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def iter_py_files(base: Path):
    for p in base.rglob("*.py"):
        # skip caches
        if "__pycache__" in p.parts:
            continue
        yield p


def check_three_line_header(p: Path) -> list[str]:
    try:
        head = p.read_text(encoding="utf-8").splitlines()[:3]
    except Exception:
        return [f"{p}: cannot read"]
    expected = ["# path:", "# version:", "# purpose:"]
    errors: list[str] = []
    if len(head) < 3:
        return [f"{p}: missing 3-line header"]
    for e, h in zip(expected, head):
        if e not in h:
            errors.append(f"{p}: header missing '{e}'")
    return errors


def check_forbidden_imports(p: Path) -> list[str]:
    if "backend" not in p.parts or "api" not in p.parts:
        return []
    txt = p.read_text(encoding="utf-8", errors="ignore")
    errs: list[str] = []
    if "import modules." in txt or "from modules." in txt:
        errs.append(f"{p}: imports from modules/ directly are forbidden (use orchestrator)")
    return errs


def check_length_limit(p: Path, limit: int = 200) -> list[str]:
    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    return [f"{p}: {len(lines)} lines exceeds {limit}"] if len(lines) > limit else []


def main() -> int:
    base = ROOT
    failed = 0
    problems: list[str] = []
    for p in iter_py_files(base):
        # Only warn for now (exit 0), but print issues
        problems += check_forbidden_imports(p)
        problems += check_three_line_header(p)
        problems += check_length_limit(p)
    if problems:
        print("\n[Architecture Lint]\n" + "\n".join(problems))
    # Return success to avoid breaking current CI; switch to 1 later
    return 0


if __name__ == "__main__":
    sys.exit(main())
