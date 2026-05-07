# Hugging Face Space (text2sql-rag)

1. Create a **Gradio** Space, Python 3.10+.
2. Vendor `src/text2sql_rag/`, `configs/default.yaml`, and **pre-built Chroma stores** *or* run indexer once at container boot (slow cold start).
3. Ship Spider `database/` + `train.json` via HF dataset attachment / release tarball — respect Spider **CC BY-SA 4.0** attribution.
4. `requirements.txt`: project deps + `gradio`.
5. Entry: `python demo/gradio_phase3.py` after copying file to `app.py` or setting working directory + `PYTHONPATH=src`.

Groq provider needs **Secrets** for `GROQ_API_KEY`; echo mode runs offline once indexes exist.
