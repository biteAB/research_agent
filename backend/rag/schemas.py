"""Schemas used by the local Markdown RAG pipeline."""
from typing import Any

from pydantic import BaseModel, Field


class RagDocument(BaseModel):
    """A Markdown document loaded from the local knowledge base."""

    doc_id: str
    report_id: str | None = None
    document_title: str = ""
    source_path: str
    source_name: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RagChunk(BaseModel):
    """A searchable chunk derived from a Markdown document."""

    chunk_uid: str
    doc_id: str
    report_id: str | None = None
    parent_id: str = ""
    document_title: str = ""
    section_title: str = ""
    section_level: int = 0
    chunk_index: int
    chunk_type: str = "section"
    source_path: str
    source_name: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RagSearchResult(BaseModel):
    """A result returned from vector search."""

    chunk_uid: str
    doc_id: str
    report_id: str | None = None
    document_title: str = ""
    section_title: str = ""
    section_level: int = 0
    chunk_index: int = 0
    chunk_type: str = "section"
    source_path: str
    source_name: str
    content: str
    score: float
