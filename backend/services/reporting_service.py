"""Reporting Service - Generates the final Markdown report with streaming."""
from typing import AsyncIterator, List, Optional
from langchain_openai import ChatOpenAI
from backend.agents.reporter import create_reporter_chain, stream_report
from backend.schemas import TaskSummary
from backend.config import settings


class ReportingService:
    """Service for generating the final research report."""

    def __init__(self):
        self.llm = self._init_llm()
        self.chain = create_reporter_chain(self.llm)

    def _init_llm(self) -> ChatOpenAI:
        """Initialize the LLM with streaming enabled."""
        return ChatOpenAI(
            api_key=settings.get_effective_api_key(),
            model=settings.get_effective_model(),
            base_url=settings.get_effective_base_url(),
            temperature=0.6,
            streaming=True
        )

    def _format_summaries(self, summaries: List[TaskSummary]) -> str:
        """Format all summaries into a single text string."""
        parts = []
        for summary in summaries:
            part = f"=== 子任务: {summary.task_id} ===\n"
            part += f"总结: {summary.summary}\n"
            part += f"核心要点:\n"
            for i, point in enumerate(summary.key_points, 1):
                part += f"  {i}. {point}\n"
            if summary.sources and any(summary.sources):
                part += f"来源: {', '.join(summary.sources)}\n"
            parts.append(part)

        return "\n".join(parts)

    async def generate_report_stream(
        self,
        topic: str,
        summaries: List[TaskSummary]
    ) -> AsyncIterator[str]:
        """Generate the final report with streaming.

        Args:
            topic: Original research topic
            summaries: List of summarized tasks

        Yields:
            Chunks of the Markdown report
        """
        summaries_text = self._format_summaries(summaries)
        async for chunk in stream_report(self.chain, topic, summaries_text):
            yield chunk


# Singleton instance
_reporting_service_instance: Optional[ReportingService] = None


def get_reporting_service() -> ReportingService:
    """Get the singleton reporting service instance."""
    global _reporting_service_instance
    if _reporting_service_instance is None:
        _reporting_service_instance = ReportingService()
    return _reporting_service_instance
