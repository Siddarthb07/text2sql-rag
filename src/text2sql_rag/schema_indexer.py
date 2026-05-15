from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

from text2sql_rag.config import AppConfig, IndexerConfig, load_config
from text2sql_rag.schema_models import DatabaseSchema
from text2sql_rag.spider_loader import load_spider_schemas


class BGESmallEmbeddingFunction(EmbeddingFunction):
    """Sentence-Transformers BGE encoder for Chroma."""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self._model_name = model_name
        self._model = SentenceTransformer(model_name)

    @staticmethod
    def name() -> str:
        """Stable id for Chroma (must be callable without instance)."""
        return "text2sql_rag_bge_sentence_transformer"

    def get_config(self) -> dict[str, Any]:
        return {"model_name": self._model_name}

    @staticmethod
    def build_from_config(config: dict[str, Any]) -> BGESmallEmbeddingFunction:
        model_name = config.get("model_name")
        if not model_name:
            raise ValueError("model_name required to rebuild BGESmallEmbeddingFunction")
        return BGESmallEmbeddingFunction(str(model_name))

    def __call__(self, input: Documents) -> Embeddings:
        texts = list(input)
        if not texts:
            return []
        vecs = self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vecs.tolist()


def _table_document(db: DatabaseSchema, table) -> tuple[str, str, dict[str, Any]]:
    """Return (id, text, metadata) for a whole-table chunk."""
    tid = f"{db.db_id}::table::{table.name_original}"
    col_bits = []
    for c in table.columns:
        t = c.type_name or ""
        col_bits.append(f"{c.name_original} ({t})" if t else c.name_original)
    cols_joined = ", ".join(col_bits) if col_bits else "(no columns parsed)"
    text = (
        f"Database {db.db_id} | Table {table.name_original} | "
        f"columns: {cols_joined}"
    )
    meta: dict[str, Any] = {
        "db_id": db.db_id,
        "kind": "table",
        "table": table.name_original,
    }
    return tid, text, meta


def _column_document(db: DatabaseSchema, table, col) -> tuple[str, str, dict[str, Any]]:
    tid = f"{db.db_id}::column::{table.name_original}.{col.name_original}"
    t = col.type_name or ""
    text = (
        f"Database {db.db_id} | Table {table.name_original} | "
        f"Column {col.name_original}" + (f" | type {t}" if t else "")
    )
    meta: dict[str, Any] = {
        "db_id": db.db_id,
        "kind": "column",
        "table": table.name_original,
        "column": col.name_original,
    }
    return tid, text, meta


def schema_to_index_chunks(
    schemas: list[DatabaseSchema],
    include_columns: bool,
    db_id_filter: set[str] | None = None,
) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    ids: list[str] = []
    docs: list[str] = []
    metas: list[dict[str, Any]] = []
    for db in schemas:
        if db_id_filter is not None and db.db_id not in db_id_filter:
            continue
        for table in db.tables:
            i, t, m = _table_document(db, table)
            ids.append(i)
            docs.append(t)
            metas.append(m)
            if include_columns:
                for col in table.columns:
                    i, t, m = _column_document(db, table, col)
                    ids.append(i)
                    docs.append(t)
                    metas.append(m)
    return ids, docs, metas


@dataclass
class IndexBuildResult:
    num_chunks: int
    collection_name: str
    persist_path: str


class SchemaIndexer:
    """Persist schema chunks in Chroma with BGE-small embeddings."""

    def __init__(self, cfg: AppConfig | None = None) -> None:
        self.cfg = cfg or load_config()
        self._embed_fn = BGESmallEmbeddingFunction(self.cfg.indexer.embedding_model)

    def _client(self, path: str | None = None) -> chromadb.api.client.ClientAPI:
        p = path or self.cfg.indexer.chroma_path
        Path(p).mkdir(parents=True, exist_ok=True)
        return chromadb.PersistentClient(path=p)

    def build_from_spider(self, *, reset: bool = True) -> IndexBuildResult:
        schemas = load_spider_schemas(self.cfg.spider.data_dir)
        flt = self.cfg.indexer.db_id_filter
        db_ids = set(flt) if flt else None
        return self.build_from_schemas(schemas, db_id_filter=db_ids, reset=reset)

    def build_from_schemas(
        self,
        schemas: list[DatabaseSchema],
        *,
        db_id_filter: set[str] | None = None,
        reset: bool = True,
        indexer_cfg: IndexerConfig | None = None,
    ) -> IndexBuildResult:
        icfg = indexer_cfg or self.cfg.indexer
        Path(icfg.chroma_path).mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=icfg.chroma_path)
        name = icfg.collection_name
        if reset:
            try:
                client.delete_collection(name)
            except Exception:
                pass
        coll = client.get_or_create_collection(
            name=name,
            embedding_function=self._embed_fn,
            metadata={"embedding_model": icfg.embedding_model},
        )
        ids, texts, metas = schema_to_index_chunks(
            schemas,
            include_columns=True,
            db_id_filter=db_id_filter,
        )
        batch = max(1, icfg.batch_size)
        for start in range(0, len(texts), batch):
            end = min(start + batch, len(texts))
            coll.add(
                ids=ids[start:end],
                documents=texts[start:end],
                metadatas=metas[start:end],
            )
        return IndexBuildResult(
            num_chunks=len(texts),
            collection_name=name,
            persist_path=icfg.chroma_path,
        )

    def get_collection(self):
        client = self._client()
        return client.get_collection(
            name=self.cfg.indexer.collection_name,
            embedding_function=self._embed_fn,
        )
