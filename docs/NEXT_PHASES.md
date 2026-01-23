# Phase 2 & 3 — Text-to-SQL RAG (next commits)

**Phase 1 (shipped):** schema indexing (Chroma + `sentence-transformers`), schema linker, SQLGlot parse validator, Spider `tables.json` loader.

## Phase 2 (implementation checklist)

1. **Few-shot retriever** — embed Spider `question`/`query` pairs; retrieve top-*k* similar NL→SQL exemplars per question.
2. **SQL generator** — call an LLM API (e.g. Groq Llama 3.1) with *frozen* system prompt + retrieved schema + few-shots. No proprietary prompts from any employer project.
3. **Validator loop** — parse with SQLGlot; optional `EXPLAIN` against SQLite; retry with error feedback (bounded retries).
4. **Execution-accuracy harness** — run predicted vs gold SQL on Spider DB snapshots; record exact-match / execution-match metrics.

## Phase 3

- Benchmark table vs baseline models (only publish numbers you actually measured).
- `writeup.md` on architecture choices.
- Optional Gradio demo on a **public** toy DB (e.g. Chinook).

Clean-room rule: **no NDA’d customer schemas or employer code paths.**
