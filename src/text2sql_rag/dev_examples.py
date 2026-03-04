"""Load Spider train/dev JSON rows (question + SQL + db_id)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_spider_qa_pairs(spider_data_dir: str | Path, json_file: str = "train.json") -> list[dict[str, Any]]:
    """
    Load Spider-format examples.

    Each entry: {"question": str, "query": str, "db_id": str, ...}
    """
    root = Path(spider_data_dir)
    path = root / json_file
    if not path.is_file():
        raise FileNotFoundError(f"Missing {path} — download Spider dataset first.")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{json_file} must be a JSON array")
    out = []
    for row in data:
        q = row.get("question")
        sql = row.get("query")
        db_id = row.get("db_id")
        if q is None or sql is None or db_id is None:
            continue
        out.append({"question": str(q), "query": str(sql).strip(), "db_id": str(db_id)})
    return out
