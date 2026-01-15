from __future__ import annotations

from text2sql_rag.sql_validator import validate_sql


def test_valid_select() -> None:
    r = validate_sql("SELECT name FROM singer WHERE country = 'France'")
    assert r.ok
    assert r.error is None


def test_invalid_sql() -> None:
    r = validate_sql("SELECT FROM WHERE")
    assert not r.ok
    assert r.error


def test_empty_sql() -> None:
    r = validate_sql("   ")
    assert not r.ok
