"""Milvus vector storage for dense/sparse hybrid RAG."""
import logging

from backend.config import settings
from backend.rag.schemas import RagChunk, RagSearchHit

logger = logging.getLogger(__name__)


class MilvusVectorStore:
    """Create, insert into, and search a Milvus collection."""

    BASE_FIELDS = {
        "chunk_uid",
        "doc_id",
        "chunk_type",
        "domain",
        "content",
        "dense_vector",
    }
    SPARSE_FIELDS = BASE_FIELDS | {"sparse_vector"}

    def __init__(self):
        from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility

        self.Collection = Collection
        self.CollectionSchema = CollectionSchema
        self.DataType = DataType
        self.FieldSchema = FieldSchema
        self.utility = utility
        self.collection_name = settings.MILVUS_COLLECTION
        self.sparse_enabled = False

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

    def _field_names(self) -> set[str]:
        return {field.name for field in self.collection.schema.fields}

    def _dense_dim(self) -> int | None:
        for field in self.collection.schema.fields:
            if field.name != "dense_vector":
                continue
            dim = field.params.get("dim") if hasattr(field, "params") else None
            return int(dim) if dim is not None else None
        return None

    def _schema_matches(self) -> bool:
        field_names = self._field_names()
        expected = self.SPARSE_FIELDS if settings.ENABLE_SPARSE_SEARCH else self.BASE_FIELDS
        if settings.ENABLE_SPARSE_SEARCH and field_names != self.SPARSE_FIELDS:
            logger.warning("Milvus sparse schema expected but not present: existing=%s", sorted(field_names))
            return False
        if not settings.ENABLE_SPARSE_SEARCH and field_names != self.BASE_FIELDS:
            logger.warning("Milvus schema mismatch: existing=%s expected=%s", sorted(field_names), sorted(expected))
            return False
        if self._dense_dim() != settings.EMBEDDING_DIM:
            logger.warning("Milvus dense dim mismatch: existing=%s expected=%s", self._dense_dim(), settings.EMBEDDING_DIM)
            return False
        self.sparse_enabled = "sparse_vector" in field_names
        return True

    def ensure_collection(self) -> None:
        if self.utility.has_collection(self.collection_name):
            self.collection = self.Collection(self.collection_name)
            if self._schema_matches():
                self.collection.load()
                logger.info("Loaded Milvus collection=%s sparse_enabled=%s", self.collection_name, self.sparse_enabled)
                return
            logger.warning("Dropping and recreating Milvus collection: %s", self.collection_name)
            try:
                self.collection.release()
            except Exception:
                logger.debug("Collection release skipped before drop", exc_info=True)
            self.utility.drop_collection(self.collection_name)

        if settings.ENABLE_SPARSE_SEARCH:
            try:
                self._create_collection(enable_sparse=True)
                return
            except Exception:
                logger.exception(
                    "Failed to create Milvus BM25 sparse collection. "
                    "Falling back to dense-only. Upgrade Milvus/pymilvus to enable SPARSE_FLOAT_VECTOR + BM25 Function."
                )
                if self.utility.has_collection(self.collection_name):
                    self.utility.drop_collection(self.collection_name)

        self._create_collection(enable_sparse=False)

    def _create_collection(self, enable_sparse: bool) -> None:
        content_kwargs = {
            "name": "content",
            "dtype": self.DataType.VARCHAR,
            "max_length": 8192,
        }
        if enable_sparse:
            content_kwargs["enable_analyzer"] = True

        fields = [
            self.FieldSchema(name="chunk_uid", dtype=self.DataType.VARCHAR, is_primary=True, max_length=64),
            self.FieldSchema(name="doc_id", dtype=self.DataType.VARCHAR, max_length=256),
            self.FieldSchema(name="chunk_type", dtype=self.DataType.VARCHAR, max_length=32),
            self.FieldSchema(name="domain", dtype=self.DataType.VARCHAR, max_length=32),
            self.FieldSchema(**content_kwargs),
            self.FieldSchema(name="dense_vector", dtype=self.DataType.FLOAT_VECTOR, dim=settings.EMBEDDING_DIM),
        ]

        if enable_sparse:
            if not hasattr(self.DataType, "SPARSE_FLOAT_VECTOR"):
                raise RuntimeError("Current pymilvus DataType has no SPARSE_FLOAT_VECTOR")
            fields.append(self.FieldSchema(name="sparse_vector", dtype=self.DataType.SPARSE_FLOAT_VECTOR))

        schema = self.CollectionSchema(fields=fields, description="Research agent Markdown chunks v2")

        if enable_sparse:
            from pymilvus import Function, FunctionType

            bm25_function = Function(
                name="content_bm25_emb",
                input_field_names=["content"],
                output_field_names=["sparse_vector"],
                function_type=FunctionType.BM25,
            )
            if not hasattr(schema, "add_function"):
                raise RuntimeError("Current pymilvus CollectionSchema has no add_function")
            schema.add_function(bm25_function)

        logger.info("Creating Milvus collection=%s sparse=%s", self.collection_name, enable_sparse)
        self.collection = self.Collection(self.collection_name, schema=schema)
        self.collection.create_index(
            field_name="dense_vector",
            index_params={
                "index_type": "HNSW",
                "metric_type": "COSINE",
                "params": {"M": 8, "efConstruction": 64},
            },
        )
        if enable_sparse:
            self.collection.create_index(
                field_name="sparse_vector",
                index_params={
                    "index_type": "SPARSE_INVERTED_INDEX",
                    "metric_type": "BM25",
                    "params": {"inverted_index_algo": "DAAT_MAXSCORE", "bm25_k1": 1.2, "bm25_b": 0.75},
                },
            )
        self.collection.load()
        self.sparse_enabled = enable_sparse

    def insert_chunks(self, chunks: list[RagChunk], dense_embeddings: list[list[float]]) -> int:
        if not chunks:
            return 0
        if len(chunks) != len(dense_embeddings):
            raise ValueError("chunks and dense_embeddings length mismatch")
        if dense_embeddings and len(dense_embeddings[0]) != settings.EMBEDDING_DIM:
            raise ValueError(
                f"Embedding dimension mismatch: expected {settings.EMBEDDING_DIM}, got {len(dense_embeddings[0])}"
            )

        rows = [
            {
                "chunk_uid": chunk.chunk_uid,
                "doc_id": chunk.doc_id,
                "chunk_type": chunk.chunk_type,
                "domain": chunk.domain,
                "content": chunk.content[:8192],
                "dense_vector": dense_vector,
            }
            for chunk, dense_vector in zip(chunks, dense_embeddings)
        ]

        logger.info("Inserting %d chunks into Milvus sparse_enabled=%s", len(rows), self.sparse_enabled)
        self.collection.insert(rows)
        self.collection.flush()
        return len(rows)

    def _hit_to_result(self, hit, source: str) -> RagSearchHit:
        entity = hit.entity
        return RagSearchHit(
            chunk_uid=entity.get("chunk_uid") or "",
            doc_id=entity.get("doc_id") or "",
            chunk_type=entity.get("chunk_type") or "",
            domain=entity.get("domain") or "",
            content=entity.get("content") or "",
            score=float(hit.score),
            source=source,
        )

    def dense_search(self, query_embedding: list[float], top_k: int, expr: str | None = None) -> list[RagSearchHit]:
        logger.info("Dense search top_k=%d expr=%s", top_k, expr)
        results = self.collection.search(
            data=[query_embedding],
            anns_field="dense_vector",
            param={"metric_type": "COSINE", "params": {"ef": 32}},
            limit=top_k,
            expr=expr,
            output_fields=["chunk_uid", "doc_id", "chunk_type", "domain", "content"],
        )
        return [self._hit_to_result(hit, "dense") for hit in results[0]]

    def sparse_search(self, query_text: str, top_k: int, expr: str | None = None) -> list[RagSearchHit]:
        if not self.sparse_enabled:
            logger.warning("Sparse search requested but Milvus BM25 sparse collection is not enabled")
            return []

        logger.info("Sparse BM25 search top_k=%d expr=%s", top_k, expr)
        results = self.collection.search(
            data=[query_text],
            anns_field="sparse_vector",
            param={"metric_type": "BM25", "params": {}},
            limit=top_k,
            expr=expr,
            output_fields=["chunk_uid", "doc_id", "chunk_type", "domain", "content"],
        )
        return [self._hit_to_result(hit, "sparse") for hit in results[0]]
