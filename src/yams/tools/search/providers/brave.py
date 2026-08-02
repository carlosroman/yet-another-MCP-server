from __future__ import annotations

from typing import Literal

import httpx

from yams.config.settings import SearchSettings
from yams.tools.search.providers.base import (
    SearchProvider,
    SearchResponse,
    SearchResult,
)

BRAVE_API_URLS = {
    "web": "https://api.search.brave.com/res/v1/web/search",
    "news": "https://api.search.brave.com/res/v1/news/search",
    "images": "https://api.search.brave.com/res/v1/images/search",
    "videos": "https://api.search.brave.com/res/v1/videos/search",
}


class BraveSearchProvider(SearchProvider):
    def __init__(self, settings: SearchSettings):
        self._api_key = settings.brave_api_key
        self._country = settings.country
        self._language = settings.language

    async def search(
        self,
        query: str,
        count: int = 10,
        search_type: Literal["web", "news", "images", "videos"] = "web",
    ) -> SearchResponse:
        url = BRAVE_API_URLS.get(search_type)
        if url is None:
            raise ValueError(f"Unsupported search type: {search_type}")

        params = {
            "q": query,
            "count": count,
            "country": self._country,
            "lang": self._language,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                headers={
                    "X-Subscription-Token": self._api_key,
                    "Accept": "application/json",
                },
                timeout=10.0,
            )

        if response.status_code == 429:
            raise RuntimeError("Rate limit exceeded. Try again later.")
        if response.status_code == 401:
            raise RuntimeError("Invalid API key. Check BRAVE_API_KEY.")
        if response.status_code != 200:
            raise RuntimeError(f"Search API error: {response.status_code} {response.text}")

        body = response.json()
        results = self._parse_results(body, search_type)

        return SearchResponse(
            query=query,
            results=results,
            total_results=len(results),
            search_type=search_type,
            provider="brave",
        )

    def _parse_results(self, body: dict, search_type: str) -> list[SearchResult]:
        results: list[SearchResult] = []

        if search_type == "web":
            for item in body.get("web", {}).get("results", []):
                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("description", ""),
                        score=0.0,
                    )
                )
        elif search_type == "news" or search_type == "images" or search_type == "videos":
            for item in body.get("results", []):
                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("description", ""),
                        score=0.0,
                    )
                )

        return results
