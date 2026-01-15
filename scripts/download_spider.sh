#!/usr/bin/env bash
# Fetch Spider 1.0 dataset (CC BY-SA 4.0) into ./data/spider by default.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${DEST:-$ROOT/data}"
ZIP_NAME="${ZIP_NAME:-spider_data.zip}"
mkdir -p "$DEST"

echo "Downloading Spider archive (Google Drive mirror via gdown)..."
python -m gdown --quiet "https://drive.google.com/uc?id=1403EGqzIDoHMdQF4c9Bkyl7dZLZ5Wt6J" -O "$DEST/$ZIP_NAME"

UNZIP_DIR="$DEST/spider_unzip_$$"
rm -rf "$UNZIP_DIR"
mkdir -p "$UNZIP_DIR"
unzip -q -o "$DEST/$ZIP_NAME" -d "$UNZIP_DIR"

TABLES_JSON="$(find "$UNZIP_DIR" -name tables.json -print | head -n 1)"
if [[ -z "${TABLES_JSON}" ]]; then
  echo "Could not locate tables.json after unzip; inspect $UNZIP_DIR" >&2
  exit 1
fi

SPIDER_ROOT="$(dirname "$TABLES_JSON")"
rm -rf "${DEST}/spider"
mv "$SPIDER_ROOT" "${DEST}/spider"
rm -rf "$UNZIP_DIR"
echo "Spider unpacked to ${DEST}/spider"
echo "Set SPIDER_DATA_DIR=${DEST}/spider (or copy to .env)."
