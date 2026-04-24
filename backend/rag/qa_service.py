"""RAG question answering service."""
import asyncio
import logging
import os
from typing import AsyncIterator

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from backend.config import settings
from backend.rag.hybrid_retriever import HybridRetriever
from backend.rag.prompts import RAG_HUMAN_PROMPT, RAG_SYSTEM_PROMPT
from backend.rag.schemas import RagSearchHit, RetrievalTrace

logger = logging.getLogger(__name__)


class RagQAService:
    """Retrieve local chunks and stream an LLM answer."""

    def __init__(self):
        self.retriever: HybridRetriever | None = None
        self.llm: ChatOpenAI | None = None
        self.chain = None

    def _get_retriever(self) -> HybridRetriever:
        if self.retriever is None:
            self.retriever = HybridRetriever()
        return self.retriever

    def _get_chain(self):
        if self.chain is None:
            self.llm = ChatOpenAI(
                api_key=os.getenv("LLM_API_KEY"),
                model=os.getenv("LLM_MODEL_ID"),
                base_url=os.getenv("LLM_BASE_URL"),
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

    def _format_context(self, results: list[RagSearchHit]) -> str:
        if not results:
            return "未检索到相关本地知识库内容。"

        parts = []
        for i, item in enumerate(results, 1):
            parts.append(
                f"[{i}] 文档ID: {item.doc_id}\n"
                f"领域: {item.domain}\n"
                f"类型: {item.chunk_type}\n"
                f"检索分数: {item.score:.4f}\n"
                f"内容:\n{item.content}"
            )
        return "\n\n".join(parts)

    def search(
        self,
        question: str,
        *,
        doc_id: str | None = None,
        domain: str | None = None,
        include_references: bool | None = None,
    ) -> RetrievalTrace:
        """Return a full retrieval trace for debugging."""
        return self._get_retriever().retrieve(
            question,
            doc_id=doc_id,
            domain=domain,
            include_references=include_references,
        )

    async def stream_answer(
        self,
        question: str,
        *,
        doc_id: str | None = None,
        domain: str | None = None,
        include_references: bool | None = None,
    ) -> AsyncIterator[str]:
        logger.info("RAG question received: %s", question)
        trace = await asyncio.to_thread(
            self.search,
            question,
            doc_id=doc_id,
            domain=domain,
            include_references=include_references,
        )
        context = self._format_context(trace.selected_context)

        async for chunk in self._get_chain().astream(
            {
                "question": question,
                "context": context,
            }
        ):
            if chunk.content:
                yield chunk.content
