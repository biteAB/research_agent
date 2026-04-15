"""Structured retrieval logging helpers."""
import logging
import uuid

from backend.rag.schemas import RagSearchHit, RetrievalTrace

logger = logging.getLogger(__name__)


def new_trace_id() -> str:
    return uuid.uuid4().hex[:12]


def _preview(text: str, length: int = 140) -> str:
    text = " ".join(text.split())
    return text[:length] + ("..." if len(text) > length else "")


def log_hits(trace_id: str, label: str, hits: list[RagSearchHit]) -> None:
    logger.info("[RAG][%s] %s count=%d", trace_id, label, len(hits))
    for rank, hit in enumerate(hits, 1):
        logger.info(
            "[RAG][%s] %s rank=%d chunk_uid=%s doc_id=%s domain=%s type=%s score=%.6f preview=%s",
            trace_id,
            label,
            rank,
            hit.chunk_uid,
            hit.doc_id,
            hit.domain,
            hit.chunk_type,
            hit.score,
            _preview(hit.content),
        )


def log_trace(trace: RetrievalTrace) -> None:
    logger.info("[RAG][%s] original_query=%s", trace.trace_id, trace.original_query)
    logger.info("[RAG][%s] rewritten_query=%s", trace.trace_id, trace.rewritten_query)
    logger.info("[RAG][%s] expanded_queries=%s", trace.trace_id, trace.expanded_queries)
    logger.info("[RAG][%s] filter_expr=%s", trace.trace_id, trace.filter_expr)
    logger.info("[RAG][%s] sparse_enabled=%s rerank_enabled=%s", trace.trace_id, trace.sparse_enabled, trace.rerank_enabled)
    log_hits(trace.trace_id, "dense_hits", trace.dense_hits)
    log_hits(trace.trace_id, "sparse_hits", trace.sparse_hits)
    log_hits(trace.trace_id, "fused_hits", trace.fused_hits)
    log_hits(trace.trace_id, "reranked_hits", trace.reranked_hits)
    log_hits(trace.trace_id, "selected_context", trace.selected_context)
