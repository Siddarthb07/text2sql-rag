#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== text2sql-rag import smoke"
python -c "from text2sql_rag import __version__; print('text2sql_rag', __version__)"

echo "== pytest"
pytest -q "$@"

if [[ -n "${SPIDER_DATA_DIR:-}" ]] && [[ -f "${SPIDER_DATA_DIR}/tables.json" ]]; then
  echo "== Spider tables.json present at SPIDER_DATA_DIR"
else
  echo "== Skip full Spider check (SPIDER_DATA_DIR unset or missing tables.json)"
fi

echo "smoke_test.sh OK"
