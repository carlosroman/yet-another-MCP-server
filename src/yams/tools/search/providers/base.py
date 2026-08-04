from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal

from yams.config.settings import SearchSettings


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    score: float = 0.0


@dataclass
class SearchResponse:
    query: str
    results: list[SearchResult] = field(default_factory=list)
    total_results: int = 0
    search_type: str = "web"
    provider: str = ""


class SearchProvider(ABC):
    @abstractmethod
    async def search(
        self,
        query: str,
        count: int = 10,
        search_type: Literal["web", "news", "images", "videos"] = "web",
    ) -> SearchResponse: ...


def get_search_provider(settings: SearchSettings) -> SearchProvider:
    if settings.provider == "brave":
        if settings.mode == "brave_llm_context":
            from yams.tools.search.providers.brave_llm_context import BraveLLMContextProvider

            return BraveLLMContextProvider(settings)
        from yams.tools.search.providers.brave import BraveSearchProvider

        return BraveSearchProvider(settings)
    elif settings.provider == "searxng":
        from yams.tools.search.providers.searxng import SearxngSearchProvider

        return SearxngSearchProvider(settings)
    msg = f"Unknown search provider: {settings.provider}"
    raise ValueError(msg)
