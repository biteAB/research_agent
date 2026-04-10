"""Report Writer Agent - Integrate all summaries into a complete Markdown report."""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Any, AsyncIterator

# System prompt for the report writer
REPORTER_SYSTEM_PROMPT = """
你是一个专业的研究报告撰写专家。你需要整合所有子任务的研究结果，生成一份完整、结构清晰的 Markdown 研究报告。

原始研究主题：{topic}

以下是各个子任务的研究结果摘要，请你将它们整合成一份连贯的报告。

报告要求：
1. 格式：标准 Markdown 格式
2. 结构必须包含：
   - # 主标题（研究主题）
   - ## 执行摘要：对整个研究的简短概述
   - ## 各个章节：每个子任务对应一个章节
   - ## 结论：总结研究发现
   - ## 参考来源：列出所有参考链接
3. 内容要连贯流畅，逻辑清晰
4. 中文撰写，语言专业但易懂
5. 不要有多余的内容，保持简洁

现在开始撰写报告：
"""

def create_reporter_chain(llm: BaseChatModel) -> Any:
    """Create the Report Writer LCEL chain.

    Args:
        llm: The language model to use (should support streaming)

    Returns:
        The LCEL chain that streams Markdown output
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", REPORTER_SYSTEM_PROMPT),
        ("human", "子任务研究结果：\n\n{summaries_text}"),
    ])

    chain = prompt | llm

    return chain


async def stream_report(chain: Any, topic: str, summaries_text: str) -> AsyncIterator[str]:
    """Stream the report generation.

    Args:
        chain: The reporter chain
        topic: Original research topic
        summaries_text: Combined summaries text

    Yields:
        Chunks of the generated report
    """
    async for chunk in chain.astream({
        "topic": topic,
        "summaries_text": summaries_text
    }):
        if chunk.content:
            yield chunk.content
