from __future__ import annotations

import os

from text2sql_rag.config import AppConfig, IndexerConfig, SpiderConfig
from text2sql_rag.schema_indexer import SchemaIndexer, schema_to_index_chunks
from text2sql_rag.spider_loader import load_tables_json, parse_tables_json_row


def test_schema_to_index_chunks_counts() -> None:
    row = {
        "db_id": "x",
        "table_names_original": ["a"],
        "table_names": ["a"],
        "column_names_original": [[-1, "*"], [0, "id"], [0, "title"]],
        "column_names": [[-1, "*"], [0, "id"], [0, "title"]],
        "column_types": ["text", "text", "text"],
        "primary_keys": [],
        "foreign_keys": [],
    }
    db = parse_tables_json_row(row)
    ids, texts, metas = schema_to_index_chunks([db], include_columns=True)
    assert len(ids) == 3
    assert all(m["db_id"] == "x" for m in metas)
    assert "Table" in texts[0]


def test_indexer_builds_chroma(minimal_tables_path, monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("HF_HOME", str(tmp_path / "hf"))
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    chroma_dir = tmp_path / "chroma"
    cfg = AppConfig(
        spider=SpiderConfig(data_dir=str(minimal_tables_path.parent)),
        indexer=IndexerConfig(
            chroma_path=str(chroma_dir),
            collection_name="test_coll",
            batch_size=8,
        ),
    )
    schemas = load_tables_json(minimal_tables_path)
    ix = SchemaIndexer(cfg)
    res = ix.build_from_schemas(
        schemas,
        reset=True,
        indexer_cfg=cfg.indexer,
    )
    assert res.num_chunks >= 3
    coll = ix.get_collection()
    assert coll.count() == res.num_chunks
