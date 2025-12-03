# path: scripts/replace_module_imports.py
# version: v0.1
# purpose: Rewrite backend/api direct `from modules.*` imports to facade `from backend.core.services.modules_proxy`

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / 'backend' / 'api'
FACADE_IMPORT = 'from backend.core.services.modules_proxy import '

pattern = re.compile(r'^from\s+modules\.(\w+)\s+import\s+(.+)$')

def rewrite_line(line: str) -> str | None:
    m = pattern.match(line.strip())
    if not m:
        return None
    names = [n.strip() for n in m.group(2).split(',')]
    # Preserve commas formatting
    return FACADE_IMPORT + ', '.join(names) + '\n'

def process_file(p: Path):
    original = p.read_text(encoding='utf-8')
    changed = False
    new_lines = []
    for line in original.splitlines(keepends=True):
        repl = rewrite_line(line)
        if repl:
            new_lines.append(repl)
            changed = True
        else:
            new_lines.append(line)
    if changed:
        p.write_text(''.join(new_lines), encoding='utf-8')
        print(f"Rewrote imports in: {p.relative_to(ROOT)}")

def main():
    for p in API_DIR.rglob('*.py'):
        if '__pycache__' in p.parts:
            continue
        process_file(p)
    print('Done rewriting module imports.')

if __name__ == '__main__':
    main()
