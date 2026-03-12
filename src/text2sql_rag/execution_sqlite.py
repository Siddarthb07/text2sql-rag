"""Resolve Spider SQLite files and compare execution results."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def resolve_spider_database_file(spider_data_dir: str | Path, db_id: str) -> Path:
    """Return path to `<database>/<db_id>/*.sqlite`."""
    base = Path(spider_data_dir) / "database" / db_id
    if not base.is_dir():
        raise FileNotFoundError(f"No database folder for db_id={db_id}: {base}")
    matches = sorted(base.glob("*.sqlite"))
    if not matches:
        raise FileNotFoundError(f"No .sqlite under {base}")
    return matches[0]


def fetch_all_tuples(db_path: str | Path, sql: str) -> list[tuple]:
    """Execute SELECT (or read-only) and return rows as tuples."""
    path = Path(db_path)
    uri = f"file:{path.resolve().as_posix()}?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    try:
        cur = con.execute(sql)
        rows = cur.fetchall()
        return [tuple(r) for r in rows]
    finally:
        con.close()


def execution_match(db_path: str | Path, sql_a: str, sql_b: str) -> bool:
    """True if both queries yield identical unordered multisets of rows (sorted compare)."""
    a = sorted(fetch_all_tuples(db_path, sql_a))
    b = sorted(fetch_all_tuples(db_path, sql_b))
    return a == b
