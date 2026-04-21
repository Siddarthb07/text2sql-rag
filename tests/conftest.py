from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

import pytest
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings


class DeterministicEmbeddingFunction(EmbeddingFunction):
    """Fixed-size unit vectors derived from SHA-256(text), no transformer download."""

    def __init__(self, model_name: str = "") -> None:
        self._dim = 384

    def __call__(self, input: Documents) -> Embeddings:
        texts = list(input)
        if not texts:
            return []
        out: list[list[float]] = []
        for t in texts:
            chunk = hashlib.sha256(t.encode("utf-8")).digest()
            buf = bytearray()
            while len(buf) < self._dim:
                buf.extend(chunk)
                chunk = hashlib.sha256(chunk).digest()
            vals = [(b / 127.5) - 1.0 for b in buf[: self._dim]]
            n = math.sqrt(sum(x * x for x in vals)) or 1.0
            out.append([x / n for x in vals])
        return out


def pytest_configure(config: pytest.Config) -> None:
    if os.environ.get("TEXT2SQL_USE_REAL_EMBEDDINGS") == "1":
        return
    import text2sql_rag.fewshot_indexer as mi_fs
    import text2sql_rag.schema_indexer as mi_si
    import text2sql_rag.schema_linker as mi_sl

    mi_si.BGESmallEmbeddingFunction = DeterministicEmbeddingFunction  # type: ignore[misc, assignment]
    mi_sl.BGESmallEmbeddingFunction = DeterministicEmbeddingFunction  # type: ignore[misc, assignment]
    mi_fs.BGESmallEmbeddingFunction = DeterministicEmbeddingFunction  # type: ignore[misc, assignment]


@pytest.fixture
def minimal_tables_path(tmp_path: Path) -> Path:
    """Tiny tables.json fixture compatible with Spider schema."""
    tables = [
        {
            "db_id": "concert_singer",
            "table_names_original": ["singer", "stadium"],
            "table_names": ["singer", "stadium"],
            "column_names_original": [
                [-1, "*"],
                [0, "singer_id"],
                [0, "name"],
                [0, "country"],
                [1, "stadium_id"],
                [1, "capacity"],
                [1, "location"],
            ],
            "column_names": [
                [-1, "*"],
                [0, "singer id"],
                [0, "name"],
                [0, "country"],
                [1, "stadium id"],
                [1, "capacity"],
                [1, "location"],
            ],
            "column_types": ["text", "number", "text", "text", "number", "number", "text"],
            "primary_keys": [],
            "foreign_keys": [],
        }
    ]
    p = tmp_path / "tables.json"
    p.write_text(json.dumps(tables), encoding="utf-8")
    return p
