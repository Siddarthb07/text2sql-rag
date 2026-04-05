"""End-to-end Phase 2 demo: schema link → few-shot → generate → validate → execute."""

from __future__ import annotations

from dataclasses import dataclass

from text2sql_rag.config import AppConfig, load_config
from text2sql_rag.execution_sqlite import execution_match, resolve_spider_database_file
from text2sql_rag.fewshot_indexer import FewShotIndexer, FewShotRetriever
from text2sql_rag.schema_linker import SchemaLinker
from text2sql_rag.sql_generator import generate_sql
from text2sql_rag.sql_validator import validate_sql


@dataclass
class PipelineResult:
    db_id: str
    question: str
    gold_sql: str
    predicted_sql: str
    raw_generation: str
    parse_ok: bool
    parse_error: str | None
    exec_match: bool | None


def run_single_example(
    *,
    db_id: str,
    question: str,
    gold_sql: str,
    cfg: AppConfig | None = None,
) -> PipelineResult:
    cfg = cfg or load_config()
    linker = SchemaLinker(cfg)
    schema_ctx = linker.build_context_text(question, max_chars=6000)

    fs_retriever = FewShotRetriever(cfg)
    fewshots = fs_retriever.retrieve(question, db_id=db_id, top_k=5)

    raw, pred_sql = generate_sql(question, schema_ctx, fewshots, cfg)
    val = validate_sql(pred_sql, dialect=cfg.validator.dialect)

    exec_match: bool | None = None
    if val.ok:
        db_path = resolve_spider_database_file(cfg.spider.data_dir, db_id)
        try:
            exec_match = execution_match(db_path, gold_sql, pred_sql)
        except Exception:
            exec_match = False

    return PipelineResult(
        db_id=db_id,
        question=question,
        gold_sql=gold_sql,
        predicted_sql=pred_sql,
        raw_generation=raw,
        parse_ok=val.ok,
        parse_error=val.error,
        exec_match=exec_match,
    )


def ensure_indexes(cfg: AppConfig | None = None) -> None:
    """Build schema + few-shot Chroma collections if missing (destructive reset)."""
    cfg = cfg or load_config()
    from text2sql_rag.schema_indexer import SchemaIndexer

    SchemaIndexer(cfg).build_from_spider(reset=True)
    FewShotIndexer(cfg).build_from_spider(reset=True)
