#!/usr/bin/env python3
"""Phase 3 mini-benchmark: aggregate parse_ok and execution_match over a Spider subset."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from text2sql_rag.config import load_config
from text2sql_rag.dev_examples import load_spider_qa_pairs
from text2sql_rag.pipeline import ensure_indexes, run_single_example


def main() -> int:
    ap = argparse.ArgumentParser(description="Mini benchmark (Spider train subset)")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--build-indexes", action="store_true", help="Rebuild Chroma indexes first (slow)")
    ap.add_argument("--provider", choices=("echo", "groq"), default=None)
    ap.add_argument("--out-dir", type=Path, default=Path("results"))
    args = ap.parse_args()

    cfg = load_config()
    if args.provider:
        cfg = cfg.model_copy(
            update={"generators": cfg.generators.model_copy(update={"provider": args.provider})}
        )

    rows = load_spider_qa_pairs(cfg.spider.data_dir, cfg.fewshot.json_file)
    rng = random.Random(args.seed)
    rng.shuffle(rows)
    rows = rows[: args.limit]

    if args.build_indexes:
        ensure_indexes(cfg)

    stats = {"n": 0, "parse_ok": 0, "exec_match": 0, "exec_attempted": 0}
    for r in rows:
        out = run_single_example(db_id=r["db_id"], question=r["question"], gold_sql=r["query"], cfg=cfg)
        stats["n"] += 1
        if out.parse_ok:
            stats["parse_ok"] += 1
        if out.exec_match is not None:
            stats["exec_attempted"] += 1
            if out.exec_match:
                stats["exec_match"] += 1

    parse_rate = stats["parse_ok"] / max(stats["n"], 1)
    exec_rate = stats["exec_match"] / max(stats["exec_attempted"], 1)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "limit_requested": args.limit,
        "examples_run": stats["n"],
        "parse_ok_rate": parse_rate,
        "execution_match_rate": exec_rate,
        "execution_attempted": stats["exec_attempted"],
        "exec_matches": stats["exec_match"],
    }
    (args.out_dir / "benchmark_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    md = "\n".join(
        [
            "# text2sql-rag mini benchmark",
            "",
            f"- Examples run: **{stats['n']}**",
            f"- Parse OK rate: **{parse_rate:.3f}**",
            f"- Execution match rate (where SQLite exec succeeded): **{exec_rate:.3f}** ({stats['exec_match']}/{stats['exec_attempted']})",
            "",
            "Echo mode mostly probes retrieval + validator plumbing; Groq adds model variance (`GROQ_API_KEY`).",
            "",
        ]
    )
    (args.out_dir / "benchmark_summary.md").write_text(md, encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
