"""Dense + Milvus BM25 sparse hybrid retrieval."""
import logging

from backend.config import settings
from backend.rag.embeddings import BgeEmbeddingService
from backend.rag.milvus_store import MilvusVectorStore
from backend.rag.query_analyzer import QueryAnalyzer
from backend.rag.reranker import LocalReranker
from backend.rag.retrieval_trace import log_trace, new_trace_id
from backend.rag.schemas import RagSearchHit, RetrievalTrace

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Run query analysis, dense search, sparse search, RRF fusion and optional rerank."""

    def __init__(self):
        self.embeddings = BgeEmbeddingService()
        self.store = MilvusVectorStore()
        self.query_analyzer = QueryAnalyzer()
        self.reranker = LocalReranker()

    def _rrf_fuse(self, dense_hits: list[RagSearchHit], sparse_hits: list[RagSearchHit]) -> list[RagSearchHit]:
        scores: dict[str, float] = {}
        best_hit: dict[str, RagSearchHit] = {}

        for rank, hit in enumerate(dense_hits, 1):
            scores[hit.chunk_uid] = scores.get(hit.chunk_uid, 0.0) + 1.0 / (settings.RRF_K + rank)
            best_hit.setdefault(hit.chunk_uid, hit)

        for rank, hit in enumerate(sparse_hits, 1):
            scores[hit.chunk_uid] = scores.get(hit.chunk_uid, 0.0) + 1.0 / (settings.RRF_K + rank)
            best_hit.setdefault(hit.chunk_uid, hit)

        fused = [
            best_hit[chunk_uid].model_copy(update={"score": score, "source": "hybrid"})
            for chunk_uid, score in scores.items()
        ]
        fused.sort(key=lambda item: item.score, reverse=True)
        return fused[: settings.HYBRID_TOP_K]

    def retrieve(
        self,
        question: str,
        *,
        doc_id: str | None = None,
        domain: str | None = None,
        include_references: bool | None = None,
    ) -> RetrievalTrace:
        trace_id = new_trace_id()
        analysis = self.query_analyzer.analyze(
            question,
            doc_id=doc_id,
            domain=domain,
            include_references=include_references,
        )
        logger.info("[RAG][%s] Starting hybrid retrieval", trace_id)

        dense_query = analysis.rewritten_query or question
        dense_vector = self.embeddings.embed_query(dense_query)
        dense_hits = self.store.dense_search(dense_vector, settings.DENSE_TOP_K, expr=analysis.filter_expr)

        sparse_hits: list[RagSearchHit] = []
        if settings.ENABLE_SPARSE_SEARCH:
            sparse_query = " ".join([question, *analysis.expanded_queries]).strip()
            try:
                sparse_hits = self.store.sparse_search(sparse_query, settings.SPARSE_TOP_K, expr=analysis.filter_expr)
            except Exception:
                logger.exception("Sparse BM25 search failed, falling back to dense-only results")
                sparse_hits = []

        fused_hits = self._rrf_fuse(dense_hits, sparse_hits)
        reranked_hits = self.reranker.rerank(analysis.rewritten_query, fused_hits, settings.RERANK_TOP_K)
        selected_context = reranked_hits[: settings.RERANK_TOP_K]

        trace = RetrievalTrace(
            trace_id=trace_id,
            original_query=analysis.original_query,
            rewritten_query=analysis.rewritten_query,
            expanded_queries=analysis.expanded_queries,
            filter_expr=analysis.filter_expr,
            dense_hits=dense_hits,
            sparse_hits=sparse_hits,
            fused_hits=fused_hits,
            reranked_hits=reranked_hits,
            selected_context=selected_context,
            sparse_enabled=self.store.sparse_enabled,
            rerank_enabled=self.reranker.available,
        )
        log_trace(trace)
        return trace
