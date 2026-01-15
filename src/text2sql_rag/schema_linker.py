from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from text2sql_rag.config import AppConfig, load_config
from text2sql_rag.schema_indexer import BGESmallEmbeddingFunction, SchemaIndexer


@dataclass
class LinkedChunk:
    document: str
    metadata: dict[str, Any]
    distance: float | None


class SchemaLinker:
    """Retrieve schema chunks for a natural-language question."""

    def __init__(self, cfg: AppConfig | None = None) -> None:
        self.cfg = cfg or load_config()
        self._embed_fn = BGESmallEmbeddingFunction(self.cfg.indexer.embedding_model)
        self._indexer_bridge = SchemaIndexer(self.cfg)

    def link(self, question: str) -> list[LinkedChunk]:
        coll = self._indexer_bridge.get_collection()
        n_results = max(1, self.cfg.linker.top_k)
        q_emb = self._embed_fn([question])
        where = None
        if not self.cfg.linker.include_column_chunks:
            where = {"kind": "table"}
        res = coll.query(
            query_embeddings=q_emb,
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        out: list[LinkedChunk] = []
        docs = (res.get("documents") or [[]])[0] or []
        metas = (res.get("metadatas") or [[]])[0] or []
        dists = (res.get("distances") or [[]])[0] if res.get("distances") else None
        for i, doc in enumerate(docs):
            meta = metas[i] if i < len(metas) else {}
            dist = float(dists[i]) if dists is not None and i < len(dists) else None
            out.append(LinkedChunk(document=str(doc), metadata=dict(meta or {}), distance=dist))
        return out

    def build_context_text(self, question: str, max_chars: int = 8000) -> str:
        """Concatenate retrieved schema lines for downstream prompt packing."""
        parts: list[str] = []
        used = 0
        for chunk in self.link(question):
            line = chunk.document.strip()
            if used + len(line) + 1 > max_chars:
                break
            parts.append(line)
            used += len(line) + 1
        return "\n".join(parts)
