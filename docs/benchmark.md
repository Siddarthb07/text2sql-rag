# Phase 3 benchmark

`python -m text2sql_rag.benchmark_run` shuffles a subset of Spider `train.json`, runs the Phase 2 pipeline (schema link → few-shot → generate → validate → SQLite execution), and writes:

- `results/benchmark_summary.json`
- `results/benchmark_summary.md`

Typical invocation after indexes exist:

```bash
python -m text2sql_rag.benchmark_run --limit 50 --seed 1
```

First-time setup (slow):

```bash
python -m text2sql_rag.benchmark_run --build-indexes --limit 20
```

Interpretation tips:

- **Echo** mode mainly stresses retrieval + parsing; execution match can be non-zero if the retrieved few-shot aligns with the question.
- **Groq** requires `GROQ_API_KEY` and reflects LLM behavior on top of the same context.
