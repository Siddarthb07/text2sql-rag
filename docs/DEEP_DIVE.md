# text2sql-rag — project deep dive

Use this file when you land in the repo cold and want the **whole story**: what problem it solves, what each phase delivers, and what is **not** promised.

## Elevator pitch

**text2sql-rag** is a compact **schema-first retrieval** stack on the public [Spider](https://yale-lily.github.io/spider) benchmark:

1. **Index** schema snippets and training QA pairs into **Chroma** with sentence-transformer embeddings.
2. **Link** a natural-language question to the right tables/columns (vector search + structured chunks).
3. **Retrieve** similar `(question, SQL)` few-shot examples from the same database id when possible.
4. **Generate** SQL with either an **echo** baseline (reuse retrieved SQL shape) or **Groq** (`GROQ_API_KEY`).
5. **Validate** with **SQLGlot** and optionally **execute** against Spider’s SQLite files to compare results with gold SQL.

The shipped artifact is **reproducibility and a clear narrative**, not a leaderboard-top model.

---

## Phase map (what to open first)

| Phase | Focus | Primary entrypoints |
| --- | --- | --- |
| **1** | Spider on disk + Chroma stores | `python -m text2sql_rag.cli_demo --build-indexes`, Gradio tab *Phase 1* |
| **2** | Single-example pipeline | `cli_demo`, Gradio tab *Phase 2* |
| **3** | Benchmark slice | `python -m text2sql_rag.benchmark_run`, [`docs/benchmark.md`](benchmark.md) |
| **4** | Docs / HF outline | [`docs/huggingface_space.md`](huggingface_space.md), [`README.md`](../README.md) |

---

## Mental model

```
Question + db_id
      │
      ├──► Schema linker (Chroma) ──► "schema context" text for the prompt
      │
      ├──► Few-shot retriever (Chroma) ──► similar QA chunks
      │
      └──► Generator (echo | Groq) ──► candidate SQL
                │
                ├──► SQLGlot validate (parse / dialect)
                └──► SQLite execution_match vs gold (optional)
```

**Echo** mode is intentionally naive: it stresses indexing + validation + execution plumbing without spending tokens.

**Groq** mode is where you plug in an LLM — you still get the same retrieval + validation shell.

---

## Data & licensing

- Spider remains **CC BY-SA 4.0**. Host copies locally; set `SPIDER_DATA_DIR` if not under `./data/spider`.
- Expected layout: `database/<db_id>/*.sqlite`, `train.json` at the Spider root (see [`README.md`](../README.md)).

---

## Honest limits

- **Execution match** is a coarse signal (result-set equality under the harness); it is not semantic equivalence for all SQL dialects.
- **Smoke-scale benchmarks** (`--limit 40`) gauge wiring, not competitive EM/F1 on the full dev split.
- **Echo** is not a general model; it exists to validate RAG plumbing offline.

---

## UI: `demo/app_gradio.py`

The Gradio **Overview** tab embeds this document. Other tabs mirror phases:

- **Phase 1** — filesystem status for Spider + Chroma paths (refresh button).
- **Phase 2** — live **schema context preview**, predicted SQL, validator status, truncated raw generation, JSON summary.
- **Phase 3–4** — benchmark + shipping commands and links.

---

## Suggested reading order

1. This file (**orientation**).
2. [`README.md`](../README.md) (**commands**).
3. [`docs/benchmark.md`](benchmark.md) if you care about aggregate metrics.
4. `src/text2sql_rag/pipeline.py` (**truth** for the single-example path).

Welcome back — if it felt like “just a script,” open **Phase 2** in the UI: the **schema context** panel shows what the linker actually feeds the generator.
