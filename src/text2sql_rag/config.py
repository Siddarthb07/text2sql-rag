from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field


class SpiderConfig(BaseModel):
    data_dir: str = "./data/spider"


class IndexerConfig(BaseModel):
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    chroma_path: str = "./data/chroma_schema"
    collection_name: str = "spider_schema"
    batch_size: int = 32
    db_id_filter: Optional[List[str]] = None


class LinkerConfig(BaseModel):
    top_k: int = 12
    include_column_chunks: bool = True


class ValidatorConfig(BaseModel):
    dialect: str = "sqlite"


class EvalConfig(BaseModel):
    enabled: bool = True


class GeneratorsConfig(BaseModel):
    enabled: bool = True
    provider: str = "echo"  # echo | groq (needs GROQ_API_KEY)
    groq_model: str = "llama-3.1-70b-versatile"


class FewShotConfig(BaseModel):
    chroma_path: str = "./data/chroma_examples"
    collection_name: str = "spider_examples"
    json_file: str = "train.json"
    max_examples: int = 400
    batch_size: int = 64


class AppConfig(BaseModel):
    spider: SpiderConfig = Field(default_factory=SpiderConfig)
    indexer: IndexerConfig = Field(default_factory=IndexerConfig)
    linker: LinkerConfig = Field(default_factory=LinkerConfig)
    validator: ValidatorConfig = Field(default_factory=ValidatorConfig)
    eval: EvalConfig = Field(default_factory=EvalConfig)
    generators: GeneratorsConfig = Field(default_factory=GeneratorsConfig)
    fewshot: FewShotConfig = Field(default_factory=FewShotConfig)


def load_config(path: Optional[Union[str, Path]] = None) -> AppConfig:
    """Load YAML config; env SPIDER_DATA_DIR overrides spider.data_dir when set."""
    if path is None:
        path = Path(__file__).resolve().parents[2] / "configs" / "default.yaml"
    path = Path(path)
    raw: Dict[str, Any] = {}
    if path.is_file():
        with path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    cfg = AppConfig.model_validate(raw)
    env_spider = os.environ.get("SPIDER_DATA_DIR")
    if env_spider:
        cfg = cfg.model_copy(
            update={"spider": cfg.spider.model_copy(update={"data_dir": env_spider})}
        )
    return cfg
