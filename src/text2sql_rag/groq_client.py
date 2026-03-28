"""Groq OpenAI-compatible chat completions via stdlib (no extra deps)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def groq_chat_completion(
    *,
    api_key: str,
    model: str,
    user_prompt: str,
    temperature: float = 0.0,
    timeout_s: float = 120.0,
) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    body = json.dumps(
        {
            "model": model,
            "temperature": temperature,
            "messages": [{"role": "user", "content": user_prompt}],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Groq HTTP {e.code}: {detail}") from e

    choices = payload.get("choices") or []
    if not choices:
        raise RuntimeError(f"Groq empty choices: {payload}")
    msg = choices[0].get("message") or {}
    return str(msg.get("content") or "")


def extract_sql_block(text: str) -> str:
    """Pull ```sql ... ``` or last fenced block."""
    if "```sql" in text.lower():
        start = text.lower().index("```sql") + len("```sql")
        end = text.find("```", start)
        if end != -1:
            return text[start:end].strip()
    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 2:
            chunk = parts[1]
            if chunk.lstrip().lower().startswith("sql"):
                chunk = chunk.split("\n", 1)[1] if "\n" in chunk else ""
            return chunk.strip()
    return text.strip()
