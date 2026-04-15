"""Embedding service for the local RAG pipeline."""
import logging

from backend.config import settings

logger = logging.getLogger(__name__)


class BgeEmbeddingService:
    """HuggingFace BGE embedding wrapper."""

    def __init__(self):
        logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL_NAME)
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        logger.info("Embedding %d document chunks", len(texts))
        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        logger.info("Embedding query")
        vector = self.model.encode(
            [text],
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]
        return vector.tolist()
