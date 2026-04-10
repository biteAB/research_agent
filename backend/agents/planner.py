"""TODO Planner Agent - Decompose research topic into 3-5 subtasks."""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Any
from backend.schemas import TodoPlan

# System prompt for the planner
PLANNER_SYSTEM_PROMPT = """
你是一个专业的研究规划专家。你的职责是将用户提供的研究主题分解为 3~5 个清晰的子任务（TODO）。

要求：
1. 分解后的子任务应该覆盖研究主题的不同方面
2. 每个子任务都要有明确的研究意图
3. 每个子任务提供 1~2 个具体的搜索关键词
4. 总共输出 3~5 个子任务，不要太多也不要太少

你必须严格按照 JSON 格式输出，格式如下：
{{
  "todos": [
    {{
      "id": "task_1",
      "title": "子任务标题",
      "intent": "这个子任务的研究意图，说明我们需要通过这个子任务了解什么",
      "search_queries": ["搜索词1", "搜索词2"]
    }}
  ]
}}
"""

def create_planner_chain(llm: BaseChatModel) -> Any:
    """Create the TODO Planner LCEL chain.

    Args:
        llm: The language model to use

    Returns:
        The LCEL chain that outputs TodoPlan
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", PLANNER_SYSTEM_PROMPT),
        ("human", "研究主题：{topic}"),
    ])

    parser = JsonOutputParser(pydantic_object=TodoPlan)

    chain = prompt | llm | parser

    return chain
