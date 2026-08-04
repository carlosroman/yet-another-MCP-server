from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from yams.config.settings import SearchSettings
from yams.tools.search.providers.base import (
    SearchProvider,
    SearchResponse,
    SearchResult,
    get_search_provider,
)
from yams.tools.search.providers.brave import BraveSearchProvider
from yams.tools.search.providers.brave_llm_context import BraveLLMContextProvider


class TestSearchResult:
    def test_default_score(self):
        result = SearchResult(title="Test", url="https://test.com", snippet="A snippet")
        assert result.score == 0.0

    def test_custom_score(self):
        result = SearchResult(title="Test", url="https://test.com", snippet="A snippet", score=0.95)
        assert result.score == 0.95


class TestSearchResponse:
    def test_default_values(self):
        resp = SearchResponse(query="test")
        assert resp.query == "test"
        assert resp.results == []
        assert resp.total_results == 0
        assert resp.search_type == "web"
        assert resp.provider == ""


class TestSearchProviderABC:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            SearchProvider()  # type: ignore

    def test_must_implement_search(self):
        class IncompleteProvider(SearchProvider):
            pass

        with pytest.raises(TypeError):
            IncompleteProvider()


class TestGetSearchProvider:
    def test_brave_provider(self):
        settings = SearchSettings(provider="brave", brave_api_key="test-key")
        provider = get_search_provider(settings)
        assert isinstance(provider, BraveSearchProvider)

    def test_unknown_provider(self):
        from unittest.mock import MagicMock

        settings = MagicMock()
        settings.provider = "google"
        with pytest.raises(ValueError, match="Unknown search provider"):
            get_search_provider(settings)


class TestBraveSearchProvider:
    @pytest.fixture
    def settings(self):
        return SearchSettings(
            provider="brave",
            brave_api_key="test-key",
            country="us",
            language="en",
        )

    @pytest.fixture
    def provider(self, settings):
        return BraveSearchProvider(settings)

    @pytest.mark.asyncio
    async def test_unsupported_search_type(self, provider):
        with pytest.raises(ValueError, match="Unsupported search type"):
            await provider.search("test", search_type="maps")  # type: ignore

    @pytest.mark.asyncio
    async def test_web_search_success(self, provider):
        mock_body = {
            "web": {
                "results": [
                    {
                        "title": "Result 1",
                        "url": "https://example.com/1",
                        "description": "Description 1",
                    },
                    {
                        "title": "Result 2",
                        "url": "https://example.com/2",
                        "description": "Description 2",
                    },
                ]
            }
        }

        async def mock_transport(request: httpx.Request):
            return httpx.Response(200, json=mock_body)

        with patch("httpx.AsyncClient", return_value=AsyncMock().__aenter__.return_value):
            pass

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = httpx.Response(200, json=mock_body)
            mock_get.return_value.status_code = 200

            response = await provider.search("python async", count=5)

        assert response.query == "python async"
        assert response.provider == "brave"
        assert response.search_type == "web"
        assert response.total_results == 2
        assert len(response.results) == 2
        assert response.results[0].title == "Result 1"
        assert response.results[0].url == "https://example.com/1"

    @pytest.mark.asyncio
    async def test_api_key_error(self, provider):
        async def mock_get(*args, **kwargs):
            return httpx.Response(401, text="Unauthorized")

        with (
            patch.object(httpx.AsyncClient, "get", new=mock_get),
            pytest.raises(RuntimeError, match="Invalid API key"),
        ):
            await provider.search("test")

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, provider):
        async def mock_get(*args, **kwargs):
            return httpx.Response(429, text="Rate limited")

        with (
            patch.object(httpx.AsyncClient, "get", new=mock_get),
            pytest.raises(RuntimeError, match="Rate limit"),
        ):
            await provider.search("test")

    @pytest.mark.asyncio
    async def test_server_error(self, provider):
        async def mock_get(*args, **kwargs):
            return httpx.Response(500, text="Internal Error")

        with (
            patch.object(httpx.AsyncClient, "get", new=mock_get),
            pytest.raises(RuntimeError, match="Search API error"),
        ):
            await provider.search("test")

    @pytest.mark.asyncio
    async def test_empty_results(self, provider):
        mock_body = {"web": {"results": []}}

        async def mock_get(*args, **kwargs):
            return httpx.Response(200, json=mock_body)

        with patch.object(httpx.AsyncClient, "get", new=mock_get):
            response = await provider.search("no results")
            assert response.total_results == 0
            assert response.results == []

    @pytest.mark.asyncio
    async def test_news_search(self, provider):
        mock_body = {
            "results": [
                {
                    "title": "News 1",
                    "url": "https://news.com/1",
                    "description": "News description",
                }
            ]
        }

        async def mock_get(*args, **kwargs):
            return httpx.Response(200, json=mock_body)

        with patch.object(httpx.AsyncClient, "get", new=mock_get):
            response = await provider.search("news", search_type="news")
            assert response.search_type == "news"
            assert len(response.results) == 1
            assert response.results[0].title == "News 1"

    @pytest.mark.asyncio
    async def test_images_search(self, provider):
        mock_body = {
            "results": [
                {
                    "title": "Image 1",
                    "url": "https://img.com/1.jpg",
                    "description": "Image description",
                }
            ]
        }

        async def mock_get(*args, **kwargs):
            return httpx.Response(200, json=mock_body)

        with patch.object(httpx.AsyncClient, "get", new=mock_get):
            response = await provider.search("images", search_type="images")
            assert response.search_type == "images"
            assert len(response.results) == 1

    @pytest.mark.asyncio
    async def test_videos_search(self, provider):
        mock_body = {
            "results": [
                {
                    "title": "Video 1",
                    "url": "https://video.com/1",
                    "description": "Video description",
                }
            ]
        }

        async def mock_get(*args, **kwargs):
            return httpx.Response(200, json=mock_body)

        with patch.object(httpx.AsyncClient, "get", new=mock_get):
            response = await provider.search("videos", search_type="videos")
            assert response.search_type == "videos"
            assert len(response.results) == 1

    def test_country_language_config(self):
        settings = SearchSettings(
            provider="brave",
            brave_api_key="key",
            country="gb",
            language="fr",
        )
        provider = BraveSearchProvider(settings)
        assert provider._country == "gb"
        assert provider._language == "fr"


class TestBraveLLMContextProvider:
    @pytest.fixture
    def settings(self):
        return SearchSettings(
            provider="brave",
            mode="brave_llm_context",
            brave_api_key="test-key",
            country="us",
            language="en",
            llm_context_count=30,
            llm_context_max_tokens=16384,
        )

    @pytest.fixture
    def provider(self, settings):
        return BraveLLMContextProvider(settings)

    @pytest.mark.asyncio
    async def test_web_search_success(self, provider):
        mock_body = {
            "grounding": {
                "generic": [
                    {
                        "title": "LLM Result 1",
                        "url": "https://example.com/1",
                        "snippets": ["First chunk of text", "Second chunk of text"],
                    },
                    {
                        "title": "LLM Result 2",
                        "url": "https://example.com/2",
                        "snippets": ["Another snippet"],
                    },
                ]
            }
        }

        async def mock_get(*args, **kwargs):
            return httpx.Response(200, json=mock_body)

        with patch.object(httpx.AsyncClient, "get", new=mock_get):
            response = await provider.search("python async", count=5)

        assert response.query == "python async"
        assert response.provider == "brave_llm_context"
        assert response.search_type == "web"
        assert response.total_results == 2
        assert len(response.results) == 2
        assert response.results[0].title == "LLM Result 1"
        assert response.results[0].url == "https://example.com/1"
        assert "First chunk of text" in response.results[0].snippet
        assert "Second chunk of text" in response.results[0].snippet

    @pytest.mark.asyncio
    async def test_non_web_search_type_error(self, provider):
        with pytest.raises(ValueError, match="LLM Context mode only supports web search"):
            await provider.search("test", search_type="news")

    @pytest.mark.asyncio
    async def test_api_key_error(self, provider):
        async def mock_get(*args, **kwargs):
            return httpx.Response(401, text="Unauthorized")

        with (
            patch.object(httpx.AsyncClient, "get", new=mock_get),
            pytest.raises(RuntimeError, match="Invalid API key"),
        ):
            await provider.search("test")

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, provider):
        async def mock_get(*args, **kwargs):
            return httpx.Response(429, text="Rate limited")

        with (
            patch.object(httpx.AsyncClient, "get", new=mock_get),
            pytest.raises(RuntimeError, match="Rate limit"),
        ):
            await provider.search("test")

    @pytest.mark.asyncio
    async def test_server_error(self, provider):
        async def mock_get(*args, **kwargs):
            return httpx.Response(500, text="Internal Error")

        with (
            patch.object(httpx.AsyncClient, "get", new=mock_get),
            pytest.raises(RuntimeError, match="Search API error"),
        ):
            await provider.search("test")

    @pytest.mark.asyncio
    async def test_empty_results(self, provider):
        mock_body = {"grounding": {"generic": []}}

        async def mock_get(*args, **kwargs):
            return httpx.Response(200, json=mock_body)

        with patch.object(httpx.AsyncClient, "get", new=mock_get):
            response = await provider.search("no results")
            assert response.total_results == 0
            assert response.results == []

    def test_llm_context_config(self):
        settings = SearchSettings(
            provider="brave",
            mode="brave_llm_context",
            brave_api_key="key",
            llm_context_count=40,
            llm_context_max_tokens=20000,
        )
        provider = BraveLLMContextProvider(settings)
        assert provider._count == 40
        assert provider._max_tokens == 20000


class TestModeRouting:
    def test_default_mode_returns_brave_provider(self):
        settings = SearchSettings(
            provider="brave",
            mode="default",
            brave_api_key="test-key",
        )
        provider = get_search_provider(settings)
        assert isinstance(provider, BraveSearchProvider)

    def test_brave_llm_context_mode_returns_llm_provider(self):
        settings = SearchSettings(
            provider="brave",
            mode="brave_llm_context",
            brave_api_key="test-key",
        )
        provider = get_search_provider(settings)
        assert isinstance(provider, BraveLLMContextProvider)
