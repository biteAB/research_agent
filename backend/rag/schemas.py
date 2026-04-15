"""Schemas used by the local Markdown RAG pipeline."""
from pydantic import BaseModel, Field


class RagDocument(BaseModel):
    """A Markdown document loaded from the local knowledge base."""

    doc_id: str
    report_id: str | None = None
    document_title: str = ""
    source_path: str
    source_name: str
    content: str


class RagChunk(BaseModel):
    """A searchable Markdown structure block."""

    chunk_uid: str
    doc_id: str
    chunk_type: str = "section"  # title / section / reference
    domain: str = "其他"
    content: str


class RagSearchHit(BaseModel):
    """A single retrieval hit from dense, sparse, hybrid, or rerank stages."""

    chunk_uid: str
    doc_id: str
    chunk_type: str
    domain: str
    content: str
    score: float
    source: str = "dense"


class QueryAnalysis(BaseModel):
    """Query rewrite, expansion and filtering decisions."""

    original_query: str
    rewritten_query: str
    expanded_queries: list[str] = Field(default_factory=list)
    domain: str | None = None
    include_references: bool = False
    filter_expr: str = ""


class RetrievalTrace(BaseModel):
    """Debug payload for a RAG retrieval request."""

    trace_id: str
    original_query: str
    rewritten_query: str
    expanded_queries: list[str] = Field(default_factory=list)
    filter_expr: str = ""
    dense_hits: list[RagSearchHit] = Field(default_factory=list)
    sparse_hits: list[RagSearchHit] = Field(default_factory=list)
    fused_hits: list[RagSearchHit] = Field(default_factory=list)
    reranked_hits: list[RagSearchHit] = Field(default_factory=list)
    selected_context: list[RagSearchHit] = Field(default_factory=list)
    sparse_enabled: bool = False
    rerank_enabled: bool = False
