from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from text2sql_rag.schema_models import Column, DatabaseSchema, ForeignKey, Table


def _col_entry(col_pairs: list[Any], idx: int) -> tuple[int, str]:
    pair = col_pairs[idx]
    return int(pair[0]), str(pair[1])


def parse_tables_json_row(row: dict[str, Any]) -> DatabaseSchema:
    """
    Parse a single Spider `tables.json` object into structured tables/columns.

    Follows the common Spider schema: column_names[_original] indexed with -1 for *.
    """
    db_id = str(row["db_id"])
    table_names_orig: list[str] = [str(t) for t in row["table_names_original"]]
    table_names: list[str] = [str(t) for t in row["table_names"]]
    col_names_orig: list[list[Any]] = row["column_names_original"]
    col_names: list[list[Any]] = row["column_names"]
    col_types: list[str] = [str(t) for t in row.get("column_types", [])]

    tables: list[Table] = []
    for t_idx, (t_orig, t_clean) in enumerate(zip(table_names_orig, table_names)):
        cols: list[Column] = []
        for c_idx in range(1, len(col_names)):
            table_idx, _ = _col_entry(col_names, c_idx)
            if table_idx != t_idx:
                continue
            _, c_name = _col_entry(col_names, c_idx)
            _, c_orig = _col_entry(col_names_orig, c_idx)
            type_name = col_types[c_idx] if c_idx < len(col_types) else None
            cols.append(
                Column(
                    db_id=db_id,
                    table_idx=t_idx,
                    table_name=t_orig,
                    column_idx=c_idx,
                    name_original=c_orig,
                    name=c_name,
                    type_name=type_name,
                )
            )
        pk_raw = row.get("primary_keys", []) or []
        primary_keys = [int(x) for x in pk_raw if isinstance(x, int)]
        tables.append(
            Table(
                db_id=db_id,
                table_idx=t_idx,
                name_original=t_orig,
                name=t_clean,
                columns=cols,
                primary_keys=primary_keys,
            )
        )

    fk_out: list[ForeignKey] = []
    for pair in row.get("foreign_keys", []) or []:
        if len(pair) != 2:
            continue
        fk_out.append(ForeignKey(child_column_idx=int(pair[0]), parent_column_idx=int(pair[1])))

    return DatabaseSchema(db_id=db_id, tables=tables, foreign_keys=fk_out)


def load_tables_json(path: str | Path) -> list[DatabaseSchema]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("tables.json must be a JSON array")
    return [parse_tables_json_row(row) for row in data]


def load_spider_schemas(data_dir: str | Path) -> list[DatabaseSchema]:
    """Load all databases from `<data_dir>/tables.json`."""
    data_dir = Path(data_dir)
    tables_path = data_dir / "tables.json"
    if not tables_path.is_file():
        raise FileNotFoundError(f"Missing tables.json under {data_dir}")
    return load_tables_json(tables_path)
