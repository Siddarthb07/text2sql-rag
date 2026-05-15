# Demo assets

Generated **without** Spider data:

```bash
python scripts/capture_demo_assets.py
```

Produces [`assets/demo/pipeline_overview.png`](assets/demo/pipeline_overview.png).

With Spider unpacked + indexes built, add browser screenshots of:

- `python -m text2sql_rag.cli_demo --build-indexes`
- `python demo/app_gradio.py` or `text2sql-rag-ui` (after `pip install -e ".[demo]"`)

Full orientation: [`docs/DEEP_DIVE.md`](DEEP_DIVE.md).
