#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

python scripts/run_kb_refresh.py \
  --schedule daily \
  --log-file logs/kb_refresh_daily.log \
  --state-file logs/kb_refresh_state.json
