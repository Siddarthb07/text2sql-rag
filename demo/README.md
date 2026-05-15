# text2sql-rag demos

## Phased Gradio UI (recommended)

```bash
pip install -e ".[demo]"
python demo/app_gradio.py
```

Or after install:

```bash
text2sql-rag-ui
```

Tabs mirror **Phases 1–4**: Spider/Chroma status, SQL generation with **schema context preview**, benchmark notes, and doc links. Narrative: [`docs/DEEP_DIVE.md`](../docs/DEEP_DIVE.md).

**Groq:** export `GROQ_API_KEY` before selecting the Groq provider.

## Legacy script name

`demo/gradio_phase3.py` is a thin alias for `demo/app_gradio.py` (same dashboard).
