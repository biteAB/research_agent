"""Search tool wrapper for Tavily or DuckDuckGo."""
from typing import List, Tuple, Optional
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.tools import DuckDuckGoSearchRun
from backend.config import settings
from backend.schemas import TaskSearchResult


class SearchTool:
    """Wrapper for search engine (Tavily or DuckDuckGo)."""

    def __init__(self):
        self.engine = settings.SEARCH_ENGINE
        self.max_results = settings.MAX_SEARCH_RESULTS
        self.max_result_length = settings.MAX_RESULT_LENGTH

        if self.engine == "tavily":
            if not settings.TAVILY_API_KEY:
                raise ValueError("TAVILY_API_KEY is required when using Tavily search")
            self.search = TavilySearchResults(
                max_results=self.max_results,
                tavily_api_key=settings.TAVILY_API_KEY
            )
        elif self.engine == "duckduckgo":
            self.search = DuckDuckGoSearchRun()
        else:
            raise ValueError(f"Unknown search engine: {self.engine}")

    def _truncate_content(self, content: str) -> str:
        """Truncate content to max length."""
        if len(content) > self.max_result_length:
            return content[:self.max_result_length] + "..."
        return content

    async def search_query(self, query: str) -> List[TaskSearchResult]:
        """Search for a single query.

        Args:
            query: Search query

        Returns:
            List of search results
        """
        if self.engine == "tavily":
            results = await self.search.ainvoke({"query": query})
            formatted_results = []
            for result in results:
                content = self._truncate_content(result.get("content", ""))
                formatted_results.append(TaskSearchResult(
                    query=query,
                    content=content,
                    source=result.get("url", "")
                ))
            return formatted_results

        else:  # duckduckgo
            result = await self.search.ainvoke(query)
            # DuckDuckGo returns a single string, split it up reasonably
            content = self._truncate_content(str(result))
            return [TaskSearchResult(
                query=query,
                content=content,
                source=None
            )]


# Singleton instance
_search_tool_instance: Optional[SearchTool] = None


def get_search_tool() -> SearchTool:
    """Get the singleton search tool instance."""
    global _search_tool_instance
    if _search_tool_instance is None:
        _search_tool_instance = SearchTool()
    return _search_tool_instance
