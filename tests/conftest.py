from __future__ import annotations

import json
from pathlib import Path

import pytest


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
