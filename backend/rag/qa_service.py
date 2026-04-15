"""RAG question answering service."""
import asyncio
import logging
from typing import AsyncIterator

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from backend.config import settings
from backend.rag.embeddings import BgeEmbeddingService
from backend.rag.milvus_store import MilvusVectorStore
from backend.rag.prompts import RAG_HUMAN_PROMPT, RAG_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class RagQAService:
    """Retrieve local chunks and stream an LLM answer."""

    def __init__(self):
        self.embeddings: BgeEmbeddingService | None = None
        self.store: MilvusVectorStore | None = None
        self.llm: ChatOpenAI | None = None
        self.chain = None

    def _get_embeddings(self) -> BgeEmbeddingService:
        if self.embeddings is None:
            self.embeddings = BgeEmbeddingService()
        return self.embeddings

    def _get_store(self) -> MilvusVectorStore:
        if self.store is None:
            self.store = MilvusVectorStore()
        return self.store

    def _get_chain(self):
        if self.chain is None:
            self.llm = ChatOpenAI(
                api_key=settings.get_effective_api_key(),
                model=settings.get_effective_model(),
                base_url=settings.get_effective_base_url(),
                temperature=0.3,
                streaming=True,
            )
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", RAG_SYSTEM_PROMPT),
                    ("human", RAG_HUMAN_PROMPT),
                ]
            )
            self.chain = prompt | self.llm
        return self.chain

    def _format_context(self, results) -> str:
        if not results:
            return "未检索到相关本地知识库内容。"

        parts = []
        for i, item in enumerate(results, 1):
            parts.append(
                f"[{i}] 文档: {item.document_title}\n"
                f"章节: {item.section_title}\n"
                f"类型: {item.chunk_type}\n"
                f"来源: {item.source_name}\n"
                f"相关度: {item.score:.4f}\n"
                f"内容:\n{item.content}"
            )
        return "\n\n".join(parts)

    def search(self, question: str):
        """Search local knowledge chunks for a question."""
        query_embedding = self._get_embeddings().embed_query(question)
        return self._get_store().search(query_embedding, settings.RAG_TOP_K)

    async def stream_answer(self, question: str) -> AsyncIterator[str]:
        logger.info("RAG question received: %s", question)
        results = await asyncio.to_thread(self.search, question)
        context = self._format_context(results)

        async for chunk in self._get_chain().astream(
            {
                "question": question,
                "context": context,
            }
        ):
            if chunk.content:
                yield chunk.content
