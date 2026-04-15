"""Milvus vector storage for local RAG chunks."""
import logging
import time

from backend.config import settings
from backend.rag.schemas import RagChunk, RagSearchResult

logger = logging.getLogger(__name__)


class MilvusVectorStore:
    """Create, insert into, and search a Milvus collection."""

    EXPECTED_FIELD_NAMES = {
        "chunk_uid",
        "doc_id",
        "report_id",
        "parent_id",
        "document_title",
        "section_title",
        "section_level",
        "chunk_index",
        "chunk_type",
        "source_path",
        "source_name",
        "content",
        "created_at",
        "embedding",
    }

    def __init__(self):
        from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility

        self.Collection = Collection
        self.CollectionSchema = CollectionSchema
        self.DataType = DataType
        self.FieldSchema = FieldSchema
        self.utility = utility
        self.collection_name = settings.MILVUS_COLLECTION
        logger.info(
            "Connecting to Milvus: host=%s port=%s collection=%s",
            settings.MILVUS_HOST,
            settings.MILVUS_PORT,
            self.collection_name,
        )
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=str(settings.MILVUS_PORT),
        )
        self.ensure_collection()

    def _existing_embedding_dim(self) -> int | None:
        for field in self.collection.schema.fields:
            if field.name != "embedding":
                continue
            dim = field.params.get("dim") if hasattr(field, "params") else None
            return int(dim) if dim is not None else None
        return None

    def _schema_matches(self) -> bool:
        field_names = {field.name for field in self.collection.schema.fields}
        if field_names != self.EXPECTED_FIELD_NAMES:
            logger.warning(
                "Milvus collection schema mismatch: collection=%s existing_fields=%s expected_fields=%s",
                self.collection_name,
                sorted(field_names),
                sorted(self.EXPECTED_FIELD_NAMES),
            )
            return False
        existing_dim = self._existing_embedding_dim()
        if existing_dim != settings.EMBEDDING_DIM:
            logger.warning(
                "Milvus collection embedding dim mismatch: collection=%s existing=%s expected=%s",
                self.collection_name,
                existing_dim,
                settings.EMBEDDING_DIM,
            )
            return False
        return True

    def ensure_collection(self) -> None:
        if self.utility.has_collection(self.collection_name):
            self.collection = self.Collection(self.collection_name)
            if self._schema_matches():
                self.collection.load()
                logger.info("Loaded existing Milvus collection: %s", self.collection_name)
                return

            logger.warning(
                "Dropping and recreating Milvus collection with the current RAG schema: %s",
                self.collection_name,
            )
            try:
                self.collection.release()
            except Exception:
                logger.debug("Collection release skipped before drop", exc_info=True)
            self.utility.drop_collection(self.collection_name)

        logger.info("Creating Milvus collection: %s", self.collection_name)
        fields = [
            self.FieldSchema(name="chunk_uid", dtype=self.DataType.VARCHAR, is_primary=True, max_length=64),
            self.FieldSchema(name="doc_id", dtype=self.DataType.VARCHAR, max_length=256),
            self.FieldSchema(name="report_id", dtype=self.DataType.VARCHAR, max_length=64),
            self.FieldSchema(name="parent_id", dtype=self.DataType.VARCHAR, max_length=64),
            self.FieldSchema(name="document_title", dtype=self.DataType.VARCHAR, max_length=512),
            self.FieldSchema(name="section_title", dtype=self.DataType.VARCHAR, max_length=512),
            self.FieldSchema(name="section_level", dtype=self.DataType.INT64),
            self.FieldSchema(name="chunk_index", dtype=self.DataType.INT64),
            self.FieldSchema(name="chunk_type", dtype=self.DataType.VARCHAR, max_length=64),
            self.FieldSchema(name="source_path", dtype=self.DataType.VARCHAR, max_length=1024),
            self.FieldSchema(name="source_name", dtype=self.DataType.VARCHAR, max_length=255),
            self.FieldSchema(name="content", dtype=self.DataType.VARCHAR, max_length=8192),
            self.FieldSchema(name="created_at", dtype=self.DataType.INT64),
            self.FieldSchema(name="embedding", dtype=self.DataType.FLOAT_VECTOR, dim=settings.EMBEDDING_DIM),
        ]
        schema = self.CollectionSchema(fields=fields, description="Research agent Markdown chunks")
        self.collection = self.Collection(self.collection_name, schema=schema)
        self.collection.create_index(
            field_name="embedding",
            index_params={
                "index_type": "HNSW",
                "metric_type": "COSINE",
                "params": {"M": 8, "efConstruction": 64},
            },
        )
        self.collection.load()

    def insert_chunks(self, chunks: list[RagChunk], embeddings: list[list[float]]) -> int:
        if not chunks:
            return 0
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings length mismatch")
        if embeddings and len(embeddings[0]) != settings.EMBEDDING_DIM:
            raise ValueError(
                f"Embedding dimension mismatch: expected {settings.EMBEDDING_DIM}, "
                f"got {len(embeddings[0])}. Check EMBEDDING_MODEL_NAME and EMBEDDING_DIM."
            )

        now = int(time.time())
        rows = [
            {
                "chunk_uid": chunk.chunk_uid,
                "doc_id": chunk.doc_id,
                "report_id": chunk.report_id or "",
                "parent_id": chunk.parent_id,
                "document_title": chunk.document_title[:512],
                "section_title": chunk.section_title[:512],
                "section_level": chunk.section_level,
                "chunk_index": chunk.chunk_index,
                "chunk_type": chunk.chunk_type,
                "source_path": chunk.source_path,
                "source_name": chunk.source_name,
                "content": chunk.content[:8192],
                "created_at": now,
                "embedding": embedding,
            }
            for chunk, embedding in zip(chunks, embeddings)
        ]

        logger.info("Inserting %d chunks into Milvus", len(rows))
        self.collection.insert(rows)
        self.collection.flush()
        return len(rows)

    def search(self, query_embedding: list[float], top_k: int) -> list[RagSearchResult]:
        logger.info("Searching Milvus top_k=%d", top_k)
        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param={"metric_type": "COSINE", "params": {"ef": 32}},
            limit=top_k,
            output_fields=[
                "chunk_uid",
                "doc_id",
                "report_id",
                "document_title",
                "section_title",
                "section_level",
                "chunk_index",
                "chunk_type",
                "source_path",
                "source_name",
                "content",
            ],
        )

        hits: list[RagSearchResult] = []
        for hit in results[0]:
            entity = hit.entity
            report_id = entity.get("report_id") or None
            hits.append(
                RagSearchResult(
                    chunk_uid=entity.get("chunk_uid") or "",
                    doc_id=entity.get("doc_id") or "",
                    report_id=report_id,
                    document_title=entity.get("document_title") or "",
                    section_title=entity.get("section_title") or "",
                    section_level=int(entity.get("section_level") or 0),
                    chunk_index=int(entity.get("chunk_index") or 0),
                    chunk_type=entity.get("chunk_type") or "",
                    source_path=entity.get("source_path") or "",
                    source_name=entity.get("source_name") or "",
                    content=entity.get("content") or "",
                    score=float(hit.score),
                )
            )
        return hits
