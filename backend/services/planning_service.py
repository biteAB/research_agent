"""Planning Service - Calls TODO Planner Agent and handles retries."""
import os
import json
from typing import Tuple, Optional
from langchain_openai import ChatOpenAI
from backend.agents.planner import create_planner_chain
from backend.schemas import TodoPlan, TodoTask
from backend.config import settings


class PlanningService:
    """Service for planning research tasks."""

    def __init__(self):
        self.llm = self._init_llm()
        self.chain = create_planner_chain(self.llm)
        self.max_retries = settings.MAX_RETRIES

    def _init_llm(self) -> ChatOpenAI:
        """Initialize the LLM."""
        return ChatOpenAI(
            api_key=os.getenv("LLM_API_KEY"),
            model=os.getenv("LLM_MODEL_ID"),
            base_url=os.getenv("LLM_BASE_URL"),
            temperature=0.7
        )

    async def create_plan(self, topic: str) -> Tuple[Optional[TodoPlan], Optional[str]]:
        """Create a TODO plan from a research topic.

        Args:
            topic: User's research topic

        Returns:
            (TodoPlan, None) if successful, (None, error message) if failed
        """
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                result = await self.chain.ainvoke({"topic": topic})

                # Handle case where result is already a dict but needs validation
                if isinstance(result, dict):
                    # Check if todos exists and is a list
                    if "todos" not in result or not isinstance(result["todos"], list):
                        raise ValueError("Invalid output: 'todos' field missing or not a list")

                    # Ensure each todo has required fields
                    for i, todo in enumerate(result["todos"]):
                        required_fields = ["id", "title", "intent", "search_queries"]
                        for field in required_fields:
                            if field not in todo:
                                raise ValueError(f"Todo {i} missing required field: {field}")

                    # Convert to TodoPlan model
                    plan = TodoPlan.model_validate(result)

                    # Ensure we have 3-5 todos
                    if not (3 <= len(plan.todos) <= 5):
                        raise ValueError(f"Expected 3-5 todos, got {len(plan.todos)}")

                    return plan, None

            except Exception as e:
                last_error = str(e)
                continue

        return None, f"Failed after {self.max_retries + 1} attempts: {last_error}"


# Singleton instance
_planning_service_instance: Optional[PlanningService] = None


def get_planning_service() -> PlanningService:
    """Get the singleton planning service instance."""
    global _planning_service_instance
    if _planning_service_instance is None:
        _planning_service_instance = PlanningService()
    return _planning_service_instance
