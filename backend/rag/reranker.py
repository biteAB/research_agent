"""Local reranker for hybrid retrieval results."""
import logging

from backend.config import settings
from backend.rag.schemas import RagSearchHit

logger = logging.getLogger(__name__)


class LocalReranker:
    """Rerank chunks using BAAI/bge-reranker-base via sentence-transformers CrossEncoder."""

    def __init__(self):
        self.model = None
        self.available = False

    def _get_model(self):
        if self.model is None:
            from sentence_transformers import CrossEncoder

            logger.info("Loading reranker model: %s", settings.RERANK_MODEL_NAME)
            self.model = CrossEncoder(settings.RERANK_MODEL_NAME)
            self.available = True
        return self.model

    def rerank(self, query: str, hits: list[RagSearchHit], top_k: int) -> list[RagSearchHit]:
        if not settings.ENABLE_RERANK or not hits:
            if hits:
                logger.info("Rerank disabled; using hybrid retrieval order")
            return hits[:top_k]
        try:
            model = self._get_model()
            pairs = [[query, hit.content] for hit in hits]
            scores = model.predict(pairs)
            reranked: list[RagSearchHit] = []
            for hit, score in zip(hits, scores):
                reranked.append(hit.model_copy(update={"score": float(score), "source": "rerank"}))
            reranked.sort(key=lambda item: item.score, reverse=True)
            return reranked[:top_k]
        except Exception:
            logger.exception("Reranker failed, falling back to hybrid order")
            self.available = False
            return hits[:top_k]
