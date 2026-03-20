"""Few-shot example store (Chroma + same embedding model as schema indexer)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb

from text2sql_rag.config import AppConfig, FewShotConfig, load_config
from text2sql_rag.dev_examples import load_spider_qa_pairs
from text2sql_rag.schema_indexer import BGESmallEmbeddingFunction


def examples_to_chunks(rows: list[dict[str, Any]]) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    ids: list[str] = []
    docs: list[str] = []
    metas: list[dict[str, Any]] = []
    for i, row in enumerate(rows):
        q = row["question"]
        sql = row["query"]
        db_id = row["db_id"]
        tid = f"{db_id}::ex::{i}"
        text = f"Question: {q}\nSQL: {sql}"
        ids.append(tid)
        docs.append(text)
        metas.append({"db_id": db_id, "kind": "example"})
    return ids, docs, metas


class FewShotIndexer:
    """Index Spider QA pairs for retrieval."""

    def __init__(self, cfg: AppConfig | None = None) -> None:
        self.cfg = cfg or load_config()
        self._embed_fn = BGESmallEmbeddingFunction(self.cfg.indexer.embedding_model)

    def build_from_spider(self, *, reset: bool = True) -> int:
        fc = self.cfg.fewshot
        rows = load_spider_qa_pairs(self.cfg.spider.data_dir, fc.json_file)
        rows = rows[: fc.max_examples]
        ids, docs, metas = examples_to_chunks(rows)

        Path(fc.chroma_path).mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=fc.chroma_path)
        name = fc.collection_name
        if reset:
            try:
                client.delete_collection(name)
            except Exception:
                pass
        coll = client.get_or_create_collection(
            name=name,
            embedding_function=self._embed_fn,
            metadata={"source": fc.json_file},
        )
        batch = max(1, fc.batch_size)
        for start in range(0, len(docs), batch):
            end = min(start + batch, len(docs))
            coll.add(ids=ids[start:end], documents=docs[start:end], metadatas=metas[start:end])
        return len(docs)

    def get_collection(self):
        fc = self.cfg.fewshot
        client = chromadb.PersistentClient(path=fc.chroma_path)
        return client.get_collection(name=fc.collection_name, embedding_function=self._embed_fn)


class FewShotRetriever:
    def __init__(self, cfg: AppConfig | None = None) -> None:
        self.cfg = cfg or load_config()
        self._embed_fn = BGESmallEmbeddingFunction(self.cfg.indexer.embedding_model)
        self._idx = FewShotIndexer(self.cfg)

    def retrieve(self, question: str, db_id: str, top_k: int = 5) -> list[dict[str, Any]]:
        coll = self._idx.get_collection()
        q_emb = self._embed_fn([question])
        res = coll.query(
            query_embeddings=q_emb,
            n_results=max(1, top_k),
            where={"db_id": db_id, "kind": "example"},
            include=["documents", "metadatas", "distances"],
        )
        out: list[dict[str, Any]] = []
        docs = (res.get("documents") or [[]])[0] or []
        metas = (res.get("metadatas") or [[]])[0] or []
        dists = (res.get("distances") or [[]])[0] if res.get("distances") else None
        for i, doc in enumerate(docs):
            meta = dict(metas[i] if i < len(metas) else {})
            dist = float(dists[i]) if dists is not None and i < len(dists) else None
            out.append({"document": str(doc), "metadata": meta, "distance": dist})
        return out
