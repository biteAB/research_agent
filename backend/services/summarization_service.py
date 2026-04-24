"""Summarization Service - Summarizes search results for each task."""
import os
from typing import Tuple, Optional, List
from langchain_openai import ChatOpenAI
from backend.agents.summarizer import create_summarizer_chain
from backend.schemas import TodoTask, TaskSummary, TaskSearchResult
from backend.config import settings


class SummarizationService:
    """Service for summarizing search results of completed tasks."""

    def __init__(self):
        self.llm = self._init_llm()
        self.chain = create_summarizer_chain(self.llm)
        self.max_retries = settings.MAX_RETRIES

    def _init_llm(self) -> ChatOpenAI:
        """Initialize the LLM."""
        return ChatOpenAI(
            api_key=os.getenv("LLM_API_KEY"),
            model=os.getenv("LLM_MODEL_ID"),
            base_url=os.getenv("LLM_BASE_URL"),
            temperature=0.5
        )

    def _format_search_results(self, results: List[TaskSearchResult]) -> str:
        """Format search results into a single text string for the prompt."""
        formatted_parts = []
        for i, result in enumerate(results, 1):
            part = f"--- 结果 {i} ---\n"
            part += f"查询: {result.query}\n"
            if result.source:
                part += f"来源: {result.source}\n"
            part += f"内容: {result.content}\n"
            formatted_parts.append(part)

        return "\n".join(formatted_parts)

    async def summarize_task(
        self,
        task: TodoTask,
        search_results: List[TaskSearchResult]
    ) -> Tuple[Optional[TaskSummary], Optional[str]]:
        """Summarize search results for a single task.

        Args:
            task: The TODO task
            search_results: Search results from searching this task

        Returns:
            (TaskSummary, None) if successful, (None, error message) if failed
        """
        last_error = None
        search_results_text = self._format_search_results(search_results)

        for attempt in range(self.max_retries + 1):
            try:
                result = await self.chain.ainvoke({
                    "task_id": task.id,
                    "task_title": task.title,
                    "task_intent": task.intent,
                    "search_results": search_results_text
                })

                if isinstance(result, dict):
                    summary = TaskSummary.model_validate(result)
                    return summary, None

            except Exception as e:
                last_error = str(e)
                continue

        return None, f"Failed after {self.max_retries + 1} attempts: {last_error}"


# Singleton instance
_summarization_service_instance: Optional[SummarizationService] = None


def get_summarization_service() -> SummarizationService:
    """Get the singleton summarization service instance."""
    global _summarization_service_instance
    if _summarization_service_instance is None:
        _summarization_service_instance = SummarizationService()
    return _summarization_service_instance
