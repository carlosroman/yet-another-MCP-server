from __future__ import annotations

from typing import Literal

from yams.config.settings import SearchSettings
from yams.tools.search.providers.base import get_search_provider


def create_search_tool(settings: SearchSettings):
    provider = get_search_provider(settings)

    async def search(
        query: str,
        count: int = 10,
        search_type: Literal["web", "news", "images", "videos"] = "web",
    ) -> dict:
        if not query or not query.strip():
            raise ValueError("Query must not be empty")
        if count < 1 or count > 20:
            raise ValueError("Count must be between 1 and 20")

        response = await provider.search(query, count, search_type)

        return {
            "query": response.query,
            "results": [
                {
                    "title": r.title,
                    "url": r.url,
                    "snippet": r.snippet,
                    "score": r.score,
                }
                for r in response.results
            ],
            "total_results": response.total_results,
            "search_type": response.search_type,
            "provider": response.provider,
        }

    return search
