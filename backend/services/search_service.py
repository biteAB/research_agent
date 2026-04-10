"""Search Service - Handles concurrent search with caching and deduplication."""
import asyncio
from typing import List, Set, Dict, Optional
from backend.tools.search_tool import get_search_tool, SearchTool
from backend.schemas import TodoTask, TaskSearchResult
from backend.config import settings


class SearchService:
    """Service for handling searches with caching and deduplication."""

    def __init__(self):
        self.search_tool = get_search_tool()
        self.cache_enabled = settings.ENABLE_SEARCH_CACHE
        self._cache: Dict[str, List[TaskSearchResult]] = {}

    def _deduplicate_results(self, results: List[TaskSearchResult]) -> List[TaskSearchResult]:
        """Remove duplicate results based on source URL."""
        seen_sources: Set[str] = set()
        unique_results: List[TaskSearchResult] = []

        for result in results:
            source = result.source
            if source is None:
                unique_results.append(result)
                continue

            if source not in seen_sources:
                seen_sources.add(source)
                unique_results.append(result)

        return unique_results

    async def search_queries(self, queries: List[str]) -> List[TaskSearchResult]:
        """Search multiple queries concurrently.

        Args:
            queries: List of search queries

        Returns:
            Combined and deduplicated list of search results
        """
        search_tasks = []

        for query in queries:
            # Check cache first
            if query in self._cache:
                search_tasks.append(asyncio.create_task(
                    asyncio.sleep(0, result=self._cache[query])
                ))
            else:
                async def do_search(q=query):
                    results = await self.search_tool.search_query(q)
                    if self.cache_enabled:
                        self._cache[q] = results
                    return results

                search_tasks.append(asyncio.create_task(do_search()))

        # Wait for all searches to complete
        all_results_lists = await asyncio.gather(*search_tasks)

        # Flatten results
        all_results = []
        for results in all_results_lists:
            all_results.extend(results)

        # Deduplicate
        return self._deduplicate_results(all_results)

    async def search_task(self, task: TodoTask) -> List[TaskSearchResult]:
        """Search for all queries in a TODO task.

        Args:
            task: The TODO task

        Returns:
            Combined search results
        """
        return await self.search_queries(task.search_queries)

    def clear_cache(self) -> None:
        """Clear the search cache."""
        self._cache.clear()


# Singleton instance
_search_service_instance: Optional[SearchService] = None


def get_search_service() -> SearchService:
    """Get the singleton search service instance."""
    global _search_service_instance
    if _search_service_instance is None:
        _search_service_instance = SearchService()
    return _search_service_instance
