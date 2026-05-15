"""Phased Gradio dashboard: Spider paths, schema RAG, generation, benchmark hints, docs."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from text2sql_rag.config import AppConfig, load_config
from text2sql_rag.pipeline import run_single_example
from text2sql_rag.schema_linker import SchemaLinker


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_deep_dive_markdown() -> str:
    p = _repo_root() / "docs" / "DEEP_DIVE.md"
    if not p.is_file():
        return "*Add `docs/DEEP_DIVE.md` for the full narrative.*"
    return p.read_text(encoding="utf-8")


def format_disk_status(cfg: AppConfig) -> str:
    """Phase 1 panel — whether Spider + Chroma directories exist."""
    lines = [
        "### Phase 1 — Data & indexes on disk",
        "",
        "| Resource | Path | Status |",
        "| --- | --- | --- |",
    ]
    root = Path(cfg.spider.data_dir)
    train_json = root / cfg.fewshot.json_file
    tables_json = root / "tables.json"

    def cell(path: Path) -> str:
        if path.is_file():
            return "file OK"
        if path.is_dir():
            return "dir OK"
        return "**MISSING**"

    lines.append(f"| Spider root | `{root.resolve()}` | {cell(root)} |")
    lines.append(f"| `{cfg.fewshot.json_file}` | `{train_json.resolve()}` | {cell(train_json)} |")
    lines.append(f"| `tables.json` (optional) | `{tables_json.resolve()}` | {cell(tables_json)} |")

    for label, rel in (
        ("Schema Chroma", cfg.indexer.chroma_path),
        ("Few-shot Chroma", cfg.fewshot.chroma_path),
    ):
        p = Path(rel)
        st = "present" if p.is_dir() else "**MISSING — run `python -m text2sql_rag.cli_demo --build-indexes`**"
        lines.append(f"| {label} | `{p.resolve()}` | {st} |")

    lines.extend(
        [
            "",
            "_Embedding model (schema + few-shot):_ `" + cfg.indexer.embedding_model + "`",
            "",
            "**Tip:** set `SPIDER_DATA_DIR` if Spider lives outside `./data/spider`.",
        ]
    )
    return "\n".join(lines)


def run_inference(
    db_id: str,
    question: str,
    gold_sql: str,
    provider: str,
    *,
    cfg: AppConfig | None = None,
    schema_preview_chars: int = 6000,
) -> tuple[str, str, str, str, str, str]:
    """Returns predicted_sql, status, raw_generation, schema_preview, gold_note, json_summary."""
    cfg = cfg or load_config()
    db_id = db_id.strip()
    question = question.strip()
    if not db_id or not question:
        return "", "*Enter both **db_id** and **question**.*", "", "", "", "{}"

    if provider == "groq" and not os.environ.get("GROQ_API_KEY"):
        return (
            "",
            "**Groq** requires `GROQ_API_KEY` in the environment.",
            "",
            "",
            "",
            json.dumps({"error": "missing_groq_key"}, indent=2),
        )

    c = cfg
    if provider in ("echo", "groq"):
        c = c.model_copy(update={"generators": c.generators.model_copy(update={"provider": provider})})

    linker = SchemaLinker(c)
    schema_preview = linker.build_context_text(question, max_chars=schema_preview_chars)

    g = gold_sql.strip() or "SELECT 1"
    out = run_single_example(db_id=db_id, question=question, gold_sql=g, cfg=c)

    meta = (
        f"- **parse_ok:** `{out.parse_ok}`\n"
        f"- **parse_error:** `{out.parse_error}`\n"
        f"- **exec_match:** `{out.exec_match}`\n"
        f"- _(Blank gold SQL defaults to `SELECT 1` — executionMatch may be meaningless.)_"
    )
    raw = out.raw_generation[:8000]
    if len(out.raw_generation) > 8000:
        raw += "\n\n… *truncated*"

    gold_note = f"Gold SQL used for execution check: `{out.gold_sql[:500]}{'…' if len(out.gold_sql) > 500 else ''}`"

    summary: dict[str, Any] = {
        "db_id": out.db_id,
        "provider": provider,
        "parse_ok": out.parse_ok,
        "parse_error": out.parse_error,
        "exec_match": out.exec_match,
        "predicted_sql": out.predicted_sql,
    }
    return out.predicted_sql, meta, raw, schema_preview, gold_note, json.dumps(summary, indent=2)


PHASE3_MARKDOWN = """### Phase 3 — Aggregate benchmark

The UI runs **single examples**. For shuffled-slice metrics over Spider `train.json`:

```bash
python -m text2sql_rag.benchmark_run --limit 40 --seed 1
```

Artifacts land in `results/benchmark_summary.{json,md}`.

See [`docs/benchmark.md`](docs/benchmark.md) for interpretation.
"""

PHASE4_MARKDOWN = """### Phase 4 — Ship, docs, HF

**One-shot CLI demo**

```bash
pip install -e ".[dev]"
python -m text2sql_rag.cli_demo --build-indexes
```

**Gradio (this app)**

```bash
pip install -e ".[demo]"
python demo/app_gradio.py
```

**Reading order**

| Doc | Purpose |
| --- | --- |
| [`docs/DEEP_DIVE.md`](docs/DEEP_DIVE.md) | Orientation & phases |
| [`README.md`](README.md) | Quick start |
| [`docs/benchmark.md`](docs/benchmark.md) | Benchmark protocol |
| [`docs/huggingface_space.md`](docs/huggingface_space.md) | HF Space outline |
| [`docs/DEMO.md`](docs/DEMO.md) | Screenshots |

Spider data: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/legalcode).
"""


def main() -> None:
    launch()


def launch() -> None:
    try:
        import gradio as gr
    except ImportError as e:
        raise SystemExit(f"Install demo extras: pip install -e '.[demo]' ({e})") from e

    cfg = load_config()
    deep = load_deep_dive_markdown()

    def refresh_paths() -> str:
        return format_disk_status(load_config())

    def infer(db_id: str, question: str, gold_sql: str, provider: str):
        pred, meta, raw, schema_preview, gold_note, js = run_inference(
            db_id, question, gold_sql, provider, cfg=load_config()
        )
        return pred, meta, raw, schema_preview, gold_note, js

    header = (
        "# text2sql-rag — phased dashboard\n\n"
        "Walk **Phase 1 → 4** in tabs: disk/index status, **schema retrieval preview**, SQL generation (echo / Groq), "
        "benchmark pointers, and reproduction commands.\n\n"
        f"_Spider data dir (resolved):_ `{Path(cfg.spider.data_dir).resolve()}`"
    )

    with gr.Blocks(theme=gr.themes.Soft(), title="text2sql-rag") as demo:
        gr.Markdown(header)
        with gr.Tabs():
            with gr.Tab("Overview — deep dive"):
                gr.Markdown(deep)
            with gr.Tab("Phase 1 — Data & indexes"):
                out_paths = gr.Markdown(value=refresh_paths())
                gr.Button("Refresh status").click(fn=refresh_paths, outputs=out_paths)
            with gr.Tab("Phase 2 — Generate SQL"):
                db_id = gr.Text(label="db_id", placeholder="concert_singer")
                question = gr.Textbox(label="Question", lines=3, placeholder="Natural language question")
                gold_sql = gr.Textbox(
                    label="Gold SQL (optional, for execution_match)",
                    lines=3,
                    placeholder="Leave blank to only validate parse; blank defaults to SELECT 1 for exec stub",
                )
                provider = gr.Dropdown(choices=["echo", "groq"], value="echo", label="Generator provider")
                run_btn = gr.Button("Generate SQL", variant="primary")
                pred = gr.Textbox(label="Predicted SQL", lines=6)
                meta = gr.Markdown()
                raw = gr.Textbox(label="Raw model output (truncated)", lines=10)
                schema_preview = gr.Textbox(label="Retrieved schema context (prompt-sized)", lines=12)
                gold_note = gr.Markdown()
                summary_json = gr.JSON(label="Structured summary")
                run_btn.click(
                    fn=infer,
                    inputs=[db_id, question, gold_sql, provider],
                    outputs=[pred, meta, raw, schema_preview, gold_note, summary_json],
                )
            with gr.Tab("Phase 3 — Benchmark"):
                gr.Markdown(PHASE3_MARKDOWN)
            with gr.Tab("Phase 4 — Ship & docs"):
                gr.Markdown(PHASE4_MARKDOWN)

        demo.load(fn=refresh_paths, outputs=out_paths)

    demo.launch()


if __name__ == "__main__":
    launch()
