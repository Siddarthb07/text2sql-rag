#!/usr/bin/env python3
"""
Phase 3 Gradio shell — question + db_id → predicted SQL + validator + optional execution.

Requires Spider unpacked and indexes built at least once:

    python -m text2sql_rag.cli_demo --build-indexes

Install UI extra: `pip install -e ".[demo]"`

Run:

    python demo/gradio_phase3.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    try:
        import gradio as gr
    except ImportError as e:
        raise SystemExit(f"Install gradio: pip install gradio ({e})") from e

    from text2sql_rag.config import load_config
    from text2sql_rag.pipeline import run_single_example

    cfg = load_config()

    def infer(db_id: str, question: str, gold_sql: str, provider: str):
        if provider == "groq" and not os.environ.get("GROQ_API_KEY"):
            return "Set GROQ_API_KEY for Groq provider.", "", "", ""
        c = cfg
        if provider in ("echo", "groq"):
            c = c.model_copy(update={"generators": c.generators.model_copy(update={"provider": provider})})
        g = gold_sql.strip() or "SELECT 1"
        out = run_single_example(db_id=db_id.strip(), question=question.strip(), gold_sql=g, cfg=c)
        meta = f"parse_ok={out.parse_ok} exec_match={out.exec_match}\nparse_err={out.parse_error}"
        return out.predicted_sql, meta, out.raw_generation[:4000], out.gold_sql

    gr.Interface(
        fn=infer,
        inputs=[
            gr.Text(label="db_id", placeholder="concert_singer"),
            gr.Textbox(label="question", lines=2),
            gr.Textbox(label="gold_sql (optional, for execution_match)", lines=2, placeholder="leave blank to only check parse"),
            gr.Dropdown(choices=["echo", "groq"], value="echo", label="provider"),
        ],
        outputs=[
            gr.Textbox(label="predicted_sql", lines=4),
            gr.Textbox(label="status", lines=3),
            gr.Textbox(label="raw_generation (truncated)", lines=8),
            gr.Textbox(label="gold_sql_stub_note", lines=1),
        ],
        title="text2sql-rag Phase 3",
        description="Uses schema + few-shot indexes on disk. Paste gold SQL when you want meaningful execution_match; use benchmark_run for aggregate EM.",
    ).launch()


if __name__ == "__main__":
    main()
