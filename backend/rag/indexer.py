"""Index Markdown documents into Milvus."""
import logging
from pathlib import Path

from backend.rag.embeddings import BgeEmbeddingService
from backend.rag.markdown_loader import MarkdownLoader
from backend.rag.metadata_extractor import MetadataExtractor
from backend.rag.milvus_store import MilvusVectorStore
from backend.rag.text_splitter import BasicTextSplitter

logger = logging.getLogger(__name__)


class RagIndexer:
    """Markdown -> chunks -> embeddings -> Milvus."""

    def __init__(self):
        self.loader = MarkdownLoader()
        self.splitter = BasicTextSplitter()
        self.metadata_extractor = MetadataExtractor()
        self.embeddings: BgeEmbeddingService | None = None
        self.store: MilvusVectorStore | None = None

    def _get_embeddings(self) -> BgeEmbeddingService:
        if self.embeddings is None:
            self.embeddings = BgeEmbeddingService()
        return self.embeddings

    def _get_store(self) -> MilvusVectorStore:
        if self.store is None:
            self.store = MilvusVectorStore()
        return self.store

    def index_file(self, path: Path, report_id: str | None = None) -> dict:
        logger.info("Indexing markdown file: %s", path)
        doc = self.loader.load_file(path, report_id=report_id)
        chunks = self.splitter.split_document(doc)

        if not chunks:
            logger.warning("No chunks generated for file: %s", path)
            return {"indexed_files": 1, "indexed_chunks": 0}

        domain = self.metadata_extractor.extract_domain(doc.document_title, doc.content)
        chunks = [chunk.model_copy(update={"domain": domain}) for chunk in chunks]
        vectors = self._get_embeddings().embed_documents([chunk.content for chunk in chunks])
        inserted = self._get_store().insert_chunks(chunks, vectors)
        logger.info("Indexed file=%s domain=%s chunks=%d", path, domain, inserted)
        return {"indexed_files": 1, "indexed_chunks": inserted, "domain": domain}

    def index_directory(self, directory: Path) -> dict:
        logger.info("Indexing markdown directory: %s", directory)
        docs = self.loader.load_directory(directory)

        total_chunks = 0
        for doc in docs:
            chunks = self.splitter.split_document(doc)
            if not chunks:
                continue
            domain = self.metadata_extractor.extract_domain(doc.document_title, doc.content)
            chunks = [chunk.model_copy(update={"domain": domain}) for chunk in chunks]
            vectors = self._get_embeddings().embed_documents([chunk.content for chunk in chunks])
            total_chunks += self._get_store().insert_chunks(chunks, vectors)

        logger.info("Indexed files=%d chunks=%d", len(docs), total_chunks)
        return {"indexed_files": len(docs), "indexed_chunks": total_chunks}
