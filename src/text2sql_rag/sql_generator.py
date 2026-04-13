"""Generate SQLite SQL from NL question + retrieved schema + few-shot examples."""

from __future__ import annotations

import os
from typing import Any

from text2sql_rag.config import AppConfig, load_config
from text2sql_rag.groq_client import extract_sql_block, groq_chat_completion


def build_prompt(
    question: str,
    schema_context: str,
    fewshots: list[dict[str, Any]],
) -> str:
    fs_lines = []
    for i, ex in enumerate(fewshots, 1):
        fs_lines.append(f"Example {i}:\n{ex['document']}")
    fs_block = "\n\n".join(fs_lines) if fs_lines else "(no similar examples)"
    return (
        "You are a SQLite expert for the Spider benchmark.\n"
        "Write ONE valid SQLite SELECT query answering the question.\n"
        "Use only tables/columns implied by the schema context.\n"
        "Reply with SQL only inside a ```sql code fence.\n\n"
        f"Schema context:\n{schema_context}\n\n"
        f"Few-shot references:\n{fs_block}\n\n"
        f"Question:\n{question}\n"
    )


def generate_sql(
    question: str,
    schema_context: str,
    fewshots: list[dict[str, Any]],
    cfg: AppConfig | None = None,
) -> tuple[str, str]:
    """
    Returns (raw_model_output, extracted_sql).

    provider echo: returns best-effort SQL from top few-shot metadata if present.
    """
    cfg = cfg or load_config()
    prov = (cfg.generators.provider or "echo").lower()
    if prov == "echo":
        for ex in fewshots:
            doc = ex.get("document") or ""
            # Canonical few-shot chunks use a dedicated SQL line after the question.
            tail = ""
            if "\nSQL:" in doc:
                tail = doc.split("\nSQL:", 1)[1].strip()
            elif doc.lstrip().startswith("SQL:"):
                tail = doc.split("SQL:", 1)[1].strip()
            elif "SQL:" in doc:
                tail = doc.split("SQL:", 1)[1].strip()
            if tail:
                return "[echo mode] parsed few-shot document\n", tail
        return "[echo mode] no few-shot SQL; fallback", "SELECT 1"

    if prov == "groq":
        key = os.environ.get("GROQ_API_KEY", "").strip()
        if not key:
            raise RuntimeError("GROQ_API_KEY not set")
        prompt = build_prompt(question, schema_context, fewshots)
        raw = groq_chat_completion(
            api_key=key,
            model=cfg.generators.groq_model,
            user_prompt=prompt,
            temperature=0.0,
        )
        sql = extract_sql_block(raw)
        return raw, sql

    raise ValueError(f"Unknown generator provider: {prov!r}")
