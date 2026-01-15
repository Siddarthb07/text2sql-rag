from __future__ import annotations

import os

from text2sql_rag.config import AppConfig, IndexerConfig, LinkerConfig, SpiderConfig
from text2sql_rag.schema_indexer import SchemaIndexer
from text2sql_rag.schema_linker import SchemaLinker
from text2sql_rag.spider_loader import load_tables_json


def test_linker_returns_singer_table(minimal_tables_path, monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("HF_HOME", str(tmp_path / "hf"))
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    chroma_dir = tmp_path / "chroma"
    cfg = AppConfig(
        spider=SpiderConfig(data_dir=str(minimal_tables_path.parent)),
        indexer=IndexerConfig(chroma_path=str(chroma_dir), collection_name="link_coll"),
        linker=LinkerConfig(top_k=4, include_column_chunks=True),
    )
    schemas = load_tables_json(minimal_tables_path)
    SchemaIndexer(cfg).build_from_schemas(schemas, reset=True)
    linker = SchemaLinker(cfg)
    hits = linker.link("Which singers are from France?")
    texts = " ".join(h.document.lower() for h in hits)
    assert "singer" in texts
