"""Milvus vector storage for dense/sparse hybrid RAG."""
import logging

from backend.config import settings
from backend.rag.schemas import RagChunk, RagSearchHit

logger = logging.getLogger(__name__)


class MilvusVectorStore:
    """Create, insert into, and search the configured Milvus collection.

    Collection selection is explicit: change MILVUS_COLLECTION when changing
    embedding models. Existing collections are never dropped automatically.
    """

    BASE_FIELDS = {
        "chunk_uid",
        "doc_id",
        "chunk_type",
        "domain",
        "content",
        "dense_vector",
    }
    SPARSE_FIELDS = BASE_FIELDS | {"sparse_vector"}

    def __init__(self, dense_dim: int):
        if dense_dim <= 0:
            raise ValueError(f"dense_dim must be positive, got {dense_dim}")

        from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility

        self.Collection = Collection
        self.CollectionSchema = CollectionSchema
        self.DataType = DataType
        self.FieldSchema = FieldSchema
        self.utility = utility
        self.collection_name = settings.MILVUS_COLLECTION
        self.dense_dim = dense_dim
        self.sparse_enabled = False

        logger.info(
            "Connecting to Milvus: host=%s port=%s collection=%s dense_dim=%d",
            settings.MILVUS_HOST,
            settings.MILVUS_PORT,
            self.collection_name,
            self.dense_dim,
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

    def _indexed_fields(self) -> set[str]:
        try:
            return {index.field_name for index in self.collection.indexes}
        except Exception:
            logger.debug("Unable to inspect Milvus indexes for collection=%s", self.collection_name, exc_info=True)
            return set()

    def _validate_existing_collection(self) -> None:
        field_names = self._field_names()
        if field_names not in (self.BASE_FIELDS, self.SPARSE_FIELDS):
            raise RuntimeError(
                "Milvus collection schema fields mismatch: "
                f"collection={self.collection_name} existing={sorted(field_names)} "
                f"expected={sorted(self.BASE_FIELDS)} or {sorted(self.SPARSE_FIELDS)}. "
                "Existing collection was not dropped. Set MILVUS_COLLECTION to a new collection name if needed."
            )

        existing_dim = self._dense_dim()
        if existing_dim != self.dense_dim:
            raise RuntimeError(
                "Milvus collection dense_vector dimension mismatch: "
                f"collection={self.collection_name} existing_dim={existing_dim} expected_dim={self.dense_dim}. "
                "Existing collection was not dropped. Change MILVUS_COLLECTION to a new collection name, "
                "or set EMBEDDING_DIM/model path to match this collection."
            )

        indexed_fields = self._indexed_fields()
        if "dense_vector" not in indexed_fields:
            raise RuntimeError(
                "Milvus collection dense index is missing: "
                f"collection={self.collection_name} indexed_fields={sorted(indexed_fields)}. "
                "Existing collection was not dropped. Set MILVUS_COLLECTION to a new collection name if needed."
            )

        has_sparse_field = "sparse_vector" in field_names
        has_sparse_index = "sparse_vector" in indexed_fields
        self.sparse_enabled = has_sparse_field and has_sparse_index
        if has_sparse_field and not has_sparse_index:
            logger.warning(
                "Milvus collection=%s has sparse_vector field but no sparse index; sparse search will be disabled",
                self.collection_name,
            )
        if settings.ENABLE_SPARSE_SEARCH and not self.sparse_enabled:
            logger.warning(
                "Milvus collection=%s is dense-only; sparse BM25 search will be disabled",
                self.collection_name,
            )

    def ensure_collection(self) -> None:
        if self.utility.has_collection(self.collection_name):
            self.collection = self.Collection(self.collection_name)
            self._validate_existing_collection()
            self.collection.load()
            logger.info(
                "Loaded Milvus collection=%s sparse_enabled=%s dense_dim=%d",
                self.collection_name,
                self.sparse_enabled,
                self.dense_dim,
            )
            return

        self._create_collection_with_sparse_fallback()

    def _create_collection_with_sparse_fallback(self) -> None:
        if settings.ENABLE_SPARSE_SEARCH:
            try:
                self._create_collection(enable_sparse=True)
                return
            except Exception:
                logger.exception(
                    "Failed to create Milvus BM25 sparse collection=%s. "
                    "Falling back to dense-only without dropping any collection.",
                    self.collection_name,
                )
                dense_collection_name = f"{self.collection_name}_dense"
                if self.utility.has_collection(self.collection_name):
                    self.collection_name = dense_collection_name
                    logger.warning("Using dense-only fallback collection=%s", self.collection_name)
                    if self.utility.has_collection(self.collection_name):
                        self.collection = self.Collection(self.collection_name)
                        self._validate_existing_collection()
                        self.collection.load()
                        return

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
            self.FieldSchema(name="dense_vector", dtype=self.DataType.FLOAT_VECTOR, dim=self.dense_dim),
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

        logger.info(
            "Creating Milvus collection=%s sparse=%s dense_dim=%d",
            self.collection_name,
            enable_sparse,
            self.dense_dim,
        )
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

        for index, embedding in enumerate(dense_embeddings):
            if len(embedding) != self.dense_dim:
                raise ValueError(
                    f"Embedding dimension mismatch at index={index}: expected {self.dense_dim}, got {len(embedding)}"
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

        logger.info(
            "Inserting %d chunks into Milvus collection=%s sparse_enabled=%s dense_dim=%d",
            len(rows),
            self.collection_name,
            self.sparse_enabled,
            self.dense_dim,
        )
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
        if len(query_embedding) != self.dense_dim:
            raise ValueError(
                f"Query embedding dimension mismatch: expected {self.dense_dim}, got {len(query_embedding)}"
            )
        logger.info("Dense search collection=%s top_k=%d expr=%s", self.collection_name, top_k, expr)
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

        logger.info("Sparse BM25 search collection=%s top_k=%d expr=%s", self.collection_name, top_k, expr)
        results = self.collection.search(
            data=[query_text],
            anns_field="sparse_vector",
            param={"metric_type": "BM25", "params": {}},
            limit=top_k,
            expr=expr,
            output_fields=["chunk_uid", "doc_id", "chunk_type", "domain", "content"],
        )
        return [self._hit_to_result(hit, "sparse") for hit in results[0]]
