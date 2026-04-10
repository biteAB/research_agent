"""Task Summarizer Agent - Summarize search results for a single task."""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Any
from backend.schemas import TaskSummary

# System prompt for the summarizer
SUMMARIZER_SYSTEM_PROMPT = """
你是一个专业的信息总结专家。你需要根据给定的子任务信息和搜索结果，生成一份结构化的总结。

任务信息：
- 子任务标题：{task_title}
- 研究意图：{task_intent}

请完成以下工作：
1. 阅读所有搜索结果，提取与研究意图相关的关键信息
2. 生成一份 300~500 字的详细总结
3. 提取 3~5 个核心要点
4. 收集所有信息来源的 URL

要求：
- 总结必须信息准确，不要编造内容
- 只保留与研究意图相关的内容，去除无关信息
- 核心要点要简洁明了
- 必须严格按照 JSON 格式输出

输出格式如下：
{{
  "task_id": "{task_id}",
  "summary": "该子任务的详细总结（300~500字）",
  "key_points": ["要点1", "要点2", "要点3"],
  "sources": ["来源URL1", "来源URL2"]
}}
"""

def create_summarizer_chain(llm: BaseChatModel) -> Any:
    """Create the Task Summarizer LCEL chain.

    Args:
        llm: The language model to use

    Returns:
        The LCEL chain that outputs TaskSummary
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", SUMMARIZER_SYSTEM_PROMPT),
        ("human", "搜索结果如下：\n\n{search_results}"),
    ])

    parser = JsonOutputParser(pydantic_object=TaskSummary)

    chain = prompt | llm | parser

    return chain
