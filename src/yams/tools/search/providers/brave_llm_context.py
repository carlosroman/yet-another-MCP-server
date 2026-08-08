from __future__ import annotations

from typing import Literal

from curl_cffi import requests

from yams.config.settings import SearchSettings
from yams.tools.search.providers.base import (
    SearchProvider,
    SearchResponse,
    SearchResult,
)

BRAVE_LLM_CONTEXT_URL = "https://api.search.brave.com/res/v1/llm/context"


class BraveLLMContextProvider(SearchProvider):
    def __init__(self, settings: SearchSettings):
        self._api_key = settings.brave_api_key
        self._country = settings.country
        self._language = settings.language
        self._count = settings.llm_context_count
        self._max_tokens = settings.llm_context_max_tokens

    async def search(
        self,
        query: str,
        count: int = 10,
        search_type: Literal["web", "news", "images", "videos"] = "web",
    ) -> SearchResponse:
        if search_type != "web":
            raise ValueError("LLM Context mode only supports web search")

        params = {
            "q": query,
            "count": min(count, self._count),
            "maximum_number_of_tokens": self._max_tokens,
            "country": self._country,
            "search_lang": self._language,
        }

        async with requests.AsyncSession() as client:
            response = await client.get(
                BRAVE_LLM_CONTEXT_URL,
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
        results = self._parse_results(body)

        return SearchResponse(
            query=query,
            results=results,
            total_results=len(results),
            search_type="web",
            provider="brave_llm_context",
        )

    def _parse_results(self, body: dict) -> list[SearchResult]:
        results: list[SearchResult] = []
        grounding = body.get("grounding", {})
        for item in grounding.get("generic", []):
            snippets = item.get("snippets", [])
            snippet_text = "\n\n".join(snippets) if snippets else ""
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=snippet_text,
                    score=0.0,
                )
            )
        return results
