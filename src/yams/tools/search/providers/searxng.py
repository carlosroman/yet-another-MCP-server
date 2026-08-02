from __future__ import annotations

from typing import Literal

import httpx

from yams.config.settings import SearchSettings
from yams.tools.search.providers.base import (
    SearchProvider,
    SearchResponse,
    SearchResult,
)


class SearxngSearchProvider(SearchProvider):
    def __init__(self, settings: SearchSettings):
        self._base_url = settings.searxng_base_url
        self._language = settings.language

    async def search(
        self,
        query: str,
        count: int = 10,
        search_type: Literal["web", "news", "images", "videos"] = "web",
    ) -> SearchResponse:
        if search_type not in ("web", "news", "images", "videos"):
            raise ValueError(f"Unsupported search type: {search_type}")

        params = {
            "q": query,
            "format": "json",
            "language": self._language,
        }

        if search_type != "web":
            params["categories"] = search_type

        url = f"{self._base_url.rstrip('/')}/search"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                timeout=10.0,
            )

        if response.status_code != 200:
            raise RuntimeError(f"SearXNG API error: {response.status_code} {response.text}")

        body = response.json()
        results = []
        for item in body.get("results", [])[:count]:
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                    score=item.get("score", 0.0),
                )
            )

        return SearchResponse(
            query=query,
            results=results,
            total_results=len(results),
            search_type=search_type,
            provider="searxng",
        )
