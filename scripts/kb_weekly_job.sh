#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

python scripts/run_kb_refresh.py \
  --schedule weekly \
  --log-file logs/kb_refresh_weekly.log \
  --state-file logs/kb_refresh_state.json \
  --freshness-days 30
