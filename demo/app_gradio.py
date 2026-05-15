#!/usr/bin/env python3
"""
Phased Gradio UI for text2sql-rag (Phases 1–4 tabs).

Run from repo root (after `pip install -e ".[demo]"`):

    python demo/app_gradio.py

Equivalent console script (after install):

    text2sql-rag-ui
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from text2sql_rag.gradio_dashboard import launch  # noqa: E402


def main() -> None:
    launch()


if __name__ == "__main__":
    main()
