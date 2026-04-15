"""Markdown structure splitting for the local RAG pipeline."""
import hashlib
import re

from backend.config import settings
from backend.rag.schemas import RagChunk, RagDocument


class BasicTextSplitter:
    """Split Markdown reports by title and level-2 sections.

    Rules:
    - # title and overview text before the first ## -> title chunk
    - ## section + body, including any ### or deeper headings -> section chunk
    - ## references/source/link section -> reference chunk
    - no heading structure -> length-based section chunks
    """

    HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
    REFERENCE_RE = re.compile(r"(参考|引用|来源|链接|出处|references?|sources?|citation)", re.IGNORECASE)

    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None):
        self.chunk_size = chunk_size or settings.RAG_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.RAG_CHUNK_OVERLAP
        self.max_section_chars = settings.RAG_MAX_SECTION_CHARS

    def _chunk_uid(self, doc: RagDocument, index: int, content: str) -> str:
        content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
        raw_id = f"{doc.source_path}:{doc.report_id or ''}:{index}:{content_hash}"
        return hashlib.md5(raw_id.encode("utf-8")).hexdigest()

    def _build_chunk(self, doc: RagDocument, index: int, chunk_type: str, content: str) -> RagChunk:
        return RagChunk(
            chunk_uid=self._chunk_uid(doc, index, content),
            doc_id=doc.doc_id,
            chunk_type=chunk_type,
            domain="其他",
            content=content.strip(),
        )

    def _split_long_block(self, block: str) -> list[str]:
        if len(block) <= self.max_section_chars:
            return [block]

        parts: list[str] = []
        current: list[str] = []
        current_len = 0
        paragraphs = re.split(r"\n\s*\n", block)

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            if current and current_len + len(paragraph) > self.max_section_chars:
                parts.append("\n\n".join(current))
                current = []
                current_len = 0
            if len(paragraph) > self.max_section_chars:
                for start in range(0, len(paragraph), self.max_section_chars):
                    parts.append(paragraph[start:start + self.max_section_chars])
                continue
            current.append(paragraph)
            current_len += len(paragraph)

        if current:
            parts.append("\n\n".join(current))
        return parts or [block[: self.max_section_chars]]

    def _chunk_type_for_h2(self, title: str) -> str:
        return "reference" if self.REFERENCE_RE.search(title) else "section"

    def _split_markdown(self, doc: RagDocument) -> list[RagChunk]:
        text = doc.content.strip()
        headings = list(self.HEADING_RE.finditer(text))
        if not headings:
            return []

        chunks: list[RagChunk] = []
        chunk_index = 0

        h1 = next((h for h in headings if len(h.group(1)) == 1), None)
        h2s = [h for h in headings if len(h.group(1)) == 2]

        if h1:
            first_h2_start = h2s[0].start() if h2s else len(text)
            title_block = text[h1.start():first_h2_start].strip()
            if title_block:
                chunks.append(self._build_chunk(doc, chunk_index, "title", title_block))
                chunk_index += 1

        if h2s:
            for i, h2 in enumerate(h2s):
                title = h2.group(2).strip()
                next_h2_start = h2s[i + 1].start() if i + 1 < len(h2s) else len(text)
                block = text[h2.start():next_h2_start].strip()
                if not block:
                    continue
                chunk_type = self._chunk_type_for_h2(title)
                for part in self._split_long_block(block):
                    chunks.append(self._build_chunk(doc, chunk_index, chunk_type, part))
                    chunk_index += 1
            return chunks

        if h1 and len(chunks) == 0:
            chunks.append(self._build_chunk(doc, chunk_index, "title", text))
            return chunks

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
                chunks.append(self._build_chunk(doc, index, "section", content))
            if end >= len(text):
                break
            start = max(end - self.chunk_overlap, start + 1)
            index += 1
        return chunks

    def split_document(self, doc: RagDocument) -> list[RagChunk]:
        structured = self._split_markdown(doc)
        if structured:
            return structured
        return self._split_plain_text(doc)
