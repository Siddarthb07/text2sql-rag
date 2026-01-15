from __future__ import annotations

from dataclasses import dataclass

import sqlglot
from sqlglot.errors import ParseError


@dataclass
class SqlValidationResult:
    ok: bool
    error: str | None = None


def validate_sql(sql: str, dialect: str = "sqlite") -> SqlValidationResult:
    """
    Parse-only validation using SQLGlot (SQLite dialect by default).

    Does not check table/column existence against a live database.
    """
    text = (sql or "").strip()
    if not text:
        return SqlValidationResult(ok=False, error="empty SQL")
    try:
        sqlglot.parse_one(text, read=dialect)
    except ParseError as e:
        return SqlValidationResult(ok=False, error=str(e))
    except Exception as e:  # pragma: no cover - defensive
        return SqlValidationResult(ok=False, error=str(e))
    return SqlValidationResult(ok=True, error=None)
