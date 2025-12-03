# path: scripts/add_headers.py
# version: v0.1
# purpose: Add 3-line headers (# path/# version/# purpose) to Python files

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]

EXPECTED = ["# path:", "# version:", "# purpose:"]


def needs_header(text: str) -> bool:
    lines = text.splitlines()
    if len(lines) < 3:
        return True
    return not (EXPECTED[0] in lines[0] and EXPECTED[1] in lines[1] and EXPECTED[2] in lines[2])


def add_header(path: Path, version: str, purpose: str, dry_run: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    if not needs_header(text):
        return False
    rel = path.relative_to(ROOT)
    header = f"# path: {rel.as_posix()}\n# version: {version}\n# purpose: {purpose}\n"
    new_text = header + text
    if dry_run:
        print(f"DRY-RUN add header -> {rel}")
        return True
    path.write_text(new_text, encoding="utf-8")
    print(f"Added header: {rel}")
    return True


def iter_targets(paths: list[str] | None) -> Iterable[Path]:
    if paths:
        for patt in paths:
            for p in ROOT.glob(patt):
                if p.is_file() and p.suffix == ".py":
                    yield p
                elif p.is_dir():
                    yield from p.rglob("*.py")
    else:
        yield from ROOT.rglob("*.py")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Write changes (default: dry-run)")
    ap.add_argument("--version", default="v0.1", help="Version string for header")
    ap.add_argument("--purpose", default="autofill", help="Purpose line content")
    ap.add_argument("--paths", nargs="*", help="Optional globs or directories to limit scope")
    args = ap.parse_args()

    changed = 0
    for p in iter_targets(args.paths):
        if "__pycache__" in p.parts or "node_modules" in p.parts:
            continue
        try:
            changed |= bool(add_header(p, args.version, args.purpose, dry_run=not args.apply))
        except Exception as e:
            print(f"Skip {p}: {e}")
    print(f"Done. Changed={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
