"""Markdown-aware text splitting for the local RAG pipeline."""
import hashlib
import re

from backend.config import settings
from backend.rag.schemas import RagChunk, RagDocument


class BasicTextSplitter:
    """Split generated Markdown reports by headings, with a plain-text fallback.

    Generated reports usually look like:
    - # original question
    - ## section title + section body
    - ## references + links

    This splitter keeps those semantic blocks intact so later metadata filters,
    parent-child chunking, and reranking have useful fields to work with.
    """

    HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
    REFERENCES_RE = re.compile(r"(参考|引用|来源|链接|references?|sources?)", re.IGNORECASE)

    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None):
        self.chunk_size = chunk_size or settings.RAG_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.RAG_CHUNK_OVERLAP

    def _build_chunk(
        self,
        doc: RagDocument,
        *,
        content: str,
        section_title: str,
        section_level: int,
        chunk_index: int,
        chunk_type: str,
        parent_id: str = "",
    ) -> RagChunk:
        content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
        raw_id = f"{doc.source_path}:{doc.report_id or ''}:{chunk_index}:{content_hash}"
        return RagChunk(
            chunk_uid=hashlib.md5(raw_id.encode("utf-8")).hexdigest(),
            doc_id=doc.doc_id,
            report_id=doc.report_id,
            parent_id=parent_id,
            document_title=doc.document_title,
            section_title=section_title,
            section_level=section_level,
            chunk_index=chunk_index,
            chunk_type=chunk_type,
            source_path=doc.source_path,
            source_name=doc.source_name,
            content=content,
            metadata={"splitter": "markdown_heading"},
        )

    def _chunk_type_for_title(self, title: str, level: int) -> str:
        if level == 1:
            return "title"
        if self.REFERENCES_RE.search(title):
            return "references"
        return "section"

    def _split_markdown_headings(self, doc: RagDocument) -> list[RagChunk]:
        text = doc.content.strip()
        headings = list(self.HEADING_RE.finditer(text))
        if not headings:
            return []

        chunks: list[RagChunk] = []
        chunk_index = 0
        current_h1_parent_id = ""

        for index, heading in enumerate(headings):
            level = len(heading.group(1))
            title = heading.group(2).strip()
            next_start = headings[index + 1].start() if index + 1 < len(headings) else len(text)
            block = text[heading.start():next_start].strip()
            if not block:
                continue

            chunk_type = self._chunk_type_for_title(title, level)
            parent_id = current_h1_parent_id if level > 1 else ""
            chunk = self._build_chunk(
                doc,
                content=block,
                section_title=title,
                section_level=level,
                chunk_index=chunk_index,
                chunk_type=chunk_type,
                parent_id=parent_id,
            )
            chunks.append(chunk)

            if level == 1:
                current_h1_parent_id = chunk.chunk_uid
            chunk_index += 1

        return chunks

    def _split_plain_text(self, doc: RagDocument) -> list[RagChunk]:
        text = doc.content.strip()
        if not text:
            return []

        chunks: list[RagChunk] = []
        start = 0
        index = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            content = text[start:end].strip()

            if content:
                chunks.append(
                    self._build_chunk(
                        doc,
                        content=content,
                        section_title=doc.document_title,
                        section_level=0,
                        chunk_index=index,
                        chunk_type="plain",
                    )
                )

            if end >= len(text):
                break

            start = max(end - self.chunk_overlap, start + 1)
            index += 1

        return chunks

    def split_document(self, doc: RagDocument) -> list[RagChunk]:
        heading_chunks = self._split_markdown_headings(doc)
        if heading_chunks:
            return heading_chunks
        return self._split_plain_text(doc)
