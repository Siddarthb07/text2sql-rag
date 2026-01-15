"""Evaluation metrics stubs (later phases; execution match, etc.)."""

from __future__ import annotations


def exact_set_match(_predicted_sql: str, _gold_sql: str, _dialect: str = "sqlite") -> bool:
    raise NotImplementedError("Structural SQL match is not implemented in Phase 1.")


def execution_match(_db_path: str, _predicted_sql: str, _gold_sql: str) -> bool:
    raise NotImplementedError("Execution-style eval requires Spider harness wiring.")
