"""Markdown loading for local RAG indexing."""
import hashlib
import logging
import re
from pathlib import Path

from backend.rag.schemas import RagDocument

logger = logging.getLogger(__name__)


class MarkdownLoader:
    """Load Markdown files into RAG document objects."""

    def _safe_id_part(self, value: str) -> str:
        value = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", value).strip("_")
        return value[:48] or "document"

    def _extract_title(self, content: str, fallback: str) -> str:
        for line in content.splitlines():
            match = re.match(r"^\s*#\s+(.+?)\s*$", line)
            if match:
                return match.group(1).strip()
        return Path(fallback).stem

    def load_file(self, path: Path, report_id: str | None = None) -> RagDocument:
        path = path.resolve()
        logger.info("Loading markdown file: %s", path)

        content = path.read_text(encoding="utf-8")
        doc_id_seed = f"{report_id or ''}:{path}"
        doc_hash = hashlib.md5(doc_id_seed.encode("utf-8")).hexdigest()[:8]
        doc_id = f"{self._safe_id_part(path.stem)}_{doc_hash}"
        document_title = self._extract_title(content, path.name)

        return RagDocument(
            doc_id=doc_id,
            report_id=report_id,
            document_title=document_title,
            source_path=str(path),
            source_name=path.name,
            content=content,
            metadata={"suffix": path.suffix},
        )

    def load_directory(self, directory: Path) -> list[RagDocument]:
        directory = directory.resolve()
        logger.info("Loading markdown directory: %s", directory)

        if not directory.exists():
            logger.warning("Markdown directory does not exist: %s", directory)
            return []

        docs: list[RagDocument] = []
        for path in directory.rglob("*.md"):
            if not path.is_file():
                continue
            doc = self.load_file(path)
            if doc.content.strip():
                docs.append(doc)

        logger.info("Loaded %d markdown documents", len(docs))
        return docs
