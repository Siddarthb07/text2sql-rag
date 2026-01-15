from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Column(BaseModel):
    """One logical column in a Spider-style schema entry."""

    db_id: str
    table_idx: int
    table_name: str
    column_idx: int
    name_original: str
    name: str
    type_name: Optional[str] = None


class ForeignKey(BaseModel):
    child_column_idx: int
    parent_column_idx: int


class Table(BaseModel):
    db_id: str
    table_idx: int
    name_original: str
    name: str
    columns: List[Column] = Field(default_factory=list)
    primary_keys: List[int] = Field(default_factory=list)


class DatabaseSchema(BaseModel):
    """Normalized view of one database from Spider `tables.json`."""

    db_id: str
    tables: List[Table] = Field(default_factory=list)
    foreign_keys: List[ForeignKey] = Field(default_factory=list)
