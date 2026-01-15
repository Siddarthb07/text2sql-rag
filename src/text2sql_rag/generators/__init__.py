"""SQL generation stubs (Phase 2+)."""

from __future__ import annotations


def generate_sql(_question: str, _schema_context: str) -> str:
    """Reserved for LLM / prompt pipeline wiring."""
    raise NotImplementedError(
        "Generation is not implemented in Phase 1; provide schema context externally."
    )


def list_generators() -> list[str]:
    return ["generate_sql (stub)"]
