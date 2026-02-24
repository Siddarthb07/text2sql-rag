"""CLI: build indexes + run one Spider QA pair."""

from __future__ import annotations

import argparse

from text2sql_rag.dev_examples import load_spider_qa_pairs
from text2sql_rag.pipeline import ensure_indexes, run_single_example


def main() -> int:
    p = argparse.ArgumentParser(description="text2sql-rag Phase 2 demo")
    p.add_argument("--build-indexes", action="store_true", help="Rebuild Chroma schema + few-shot stores")
    p.add_argument("--db-id", type=str, default="concert_singer")
    p.add_argument("--question-index", type=int, default=0, help="Pick N-th train.json row for db-id")
    p.add_argument("--provider", type=str, choices=("echo", "groq"), default=None)
    args = p.parse_args()

    cfg_module = __import__("text2sql_rag.config", fromlist=["load_config"])
    cfg = cfg_module.load_config()
    if args.provider:
        cfg = cfg.model_copy(
            update={
                "generators": cfg.generators.model_copy(update={"provider": args.provider})
            }
        )

    rows = [r for r in load_spider_qa_pairs(cfg.spider.data_dir, cfg.fewshot.json_file) if r["db_id"] == args.db_id]
    if not rows:
        print(f"No rows for db_id={args.db_id} in {cfg.fewshot.json_file}")
        return 1
    row = rows[args.question_index % len(rows)]

    if args.build_indexes:
        print("Building indexes (reset=true)...")
        ensure_indexes(cfg)

    print(f"db_id={row['db_id']}")
    print(f"question={row['question']}")
    out = run_single_example(db_id=row["db_id"], question=row["question"], gold_sql=row["query"], cfg=cfg)
    print(f"gold_sql={out.gold_sql}")
    print(f"predicted_sql={out.predicted_sql}")
    print(f"parse_ok={out.parse_ok} err={out.parse_error}")
    print(f"exec_match={out.exec_match}")
    print("--- raw generation ---")
    print(out.raw_generation[:1500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
