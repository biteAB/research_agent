"""Embedding service for the local RAG pipeline."""
import logging
import os
from pathlib import Path

from backend.config import settings

logger = logging.getLogger(__name__)


class BgeEmbeddingService:
    """Local SentenceTransformer embedding wrapper.

    The model must be present on disk. Runtime network downloads are disabled
    deliberately so indexing/search behavior is reproducible.
    """

    def __init__(self):
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

        self.model_name = settings.EMBEDDING_MODEL_NAME
        self.model_path = self._resolve_model_path(settings.EMBEDDING_MODEL_PATH)
        if not self.model_path.exists() or not self.model_path.is_dir():
            raise FileNotFoundError(
                f"Local embedding model directory not found: {self.model_path}. "
                "Set EMBEDDING_MODEL_PATH to a valid local model directory."
            )

        logger.info(
            "Loading local embedding model: name=%s path=%s offline=true",
            self.model_name,
            self.model_path,
        )
        from sentence_transformers import SentenceTransformer

        try:
            self.model = SentenceTransformer(str(self.model_path), local_files_only=True)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load local embedding model from {self.model_path}. "
                "Runtime remote downloads are disabled; verify the model files are complete."
            ) from exc

        detected_dimension = self._detect_dimension()
        if settings.EMBEDDING_DIM != detected_dimension:
            raise RuntimeError(
                "Configured EMBEDDING_DIM does not match local model output dimension: "
                f"configured={settings.EMBEDDING_DIM} detected={detected_dimension} "
                f"model_path={self.model_path}. Update EMBEDDING_DIM or choose the correct local model."
            )
        self.dimension = settings.EMBEDDING_DIM
        logger.info(
            "Local embedding model ready: name=%s path=%s dimension=%d",
            self.model_name,
            self.model_path,
            self.dimension,
        )

    def _resolve_model_path(self, value: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        project_root = Path(__file__).resolve().parents[2]
        return (project_root / path).resolve()

    def _detect_dimension(self) -> int:
        vector = self.model.encode(
            ["embedding dimension check"],
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]
        dimension = len(vector)
        if dimension <= 0:
            raise RuntimeError(f"Invalid embedding dimension detected from local model: {dimension}")
        return dimension

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        logger.info("Embedding %d document chunks", len(texts))
        if not texts:
            return []
        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        logger.info("Embedding query with local model dimension=%d", self.dimension)
        vector = self.model.encode(
            [text],
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]
        return vector.tolist()
