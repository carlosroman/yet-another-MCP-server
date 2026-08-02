from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from yams.config.settings import SearchSettings
from yams.tools.search import create_search_tool


class TestCreateSearchTool:
    @pytest.fixture
    def settings(self):
        return SearchSettings(
            provider="brave",
            brave_api_key="test-key",
            country="us",
            language="en",
        )

    def test_returns_callable(self, settings):
        tool = create_search_tool(settings)
        assert callable(tool)

    @pytest.mark.asyncio
    async def test_empty_query_raises_error(self, settings):
        tool = create_search_tool(settings)
        with pytest.raises(ValueError, match="Query must not be empty"):
            await tool("")

    @pytest.mark.asyncio
    async def test_whitespace_only_query_raises_error(self, settings):
        tool = create_search_tool(settings)
        with pytest.raises(ValueError, match="Query must not be empty"):
            await tool("   ")

    @pytest.mark.asyncio
    async def test_count_too_low_raises_error(self, settings):
        tool = create_search_tool(settings)
        with pytest.raises(ValueError, match="Count must be between 1 and 20"):
            await tool("test", count=0)

    @pytest.mark.asyncio
    async def test_count_too_high_raises_error(self, settings):
        tool = create_search_tool(settings)
        with pytest.raises(ValueError, match="Count must be between 1 and 20"):
            await tool("test", count=21)

    @pytest.mark.asyncio
    async def test_successful_search(self, settings):
        mock_provider = AsyncMock()
        mock_provider.search = AsyncMock(
            return_value=type(
                "MockResponse",
                (),
                {
                    "query": "python",
                    "results": [
                        type(
                            "MockResult",
                            (),
                            {
                                "title": "Python",
                                "url": "https://python.org",
                                "snippet": "Python language",
                                "score": 0.95,
                            },
                        )(),
                    ],
                    "total_results": 1,
                    "search_type": "web",
                    "provider": "brave",
                },
            )()
        )

        with patch("yams.tools.search.tool.get_search_provider", return_value=mock_provider):
            tool = create_search_tool(settings)
            result = await tool("python", count=5)

        assert result["query"] == "python"
        assert len(result["results"]) == 1
        assert result["results"][0]["title"] == "Python"
        assert result["results"][0]["url"] == "https://python.org"
        assert result["total_results"] == 1
        assert result["search_type"] == "web"
        assert result["provider"] == "brave"

    @pytest.mark.asyncio
    async def test_default_count(self, settings):
        mock_provider = AsyncMock()
        mock_provider.search = AsyncMock(
            return_value=type(
                "MockResponse",
                (),
                {
                    "query": "test",
                    "results": [],
                    "total_results": 0,
                    "search_type": "web",
                    "provider": "brave",
                },
            )()
        )

        with patch("yams.tools.search.tool.get_search_provider", return_value=mock_provider):
            tool = create_search_tool(settings)
            await tool("test")

        mock_provider.search.assert_called_once_with("test", 10, "web")

    @pytest.mark.asyncio
    async def test_search_type_propagation(self, settings):
        mock_provider = AsyncMock()
        mock_provider.search = AsyncMock(
            return_value=type(
                "MockResponse",
                (),
                {
                    "query": "test",
                    "results": [],
                    "total_results": 0,
                    "search_type": "news",
                    "provider": "brave",
                },
            )()
        )

        with patch("yams.tools.search.tool.get_search_provider", return_value=mock_provider):
            tool = create_search_tool(settings)
            await tool("test", search_type="news")

        mock_provider.search.assert_called_once_with("test", 10, "news")

    @pytest.mark.asyncio
    async def test_provider_error_propagates(self, settings):
        mock_provider = AsyncMock()
        mock_provider.search = AsyncMock(side_effect=RuntimeError("API error"))

        with patch("yams.tools.search.tool.get_search_provider", return_value=mock_provider):
            tool = create_search_tool(settings)
            with pytest.raises(RuntimeError, match="API error"):
                await tool("test")

    @pytest.mark.asyncio
    async def test_empty_results(self, settings):
        mock_provider = AsyncMock()
        mock_provider.search = AsyncMock(
            return_value=type(
                "MockResponse",
                (),
                {
                    "query": "no results",
                    "results": [],
                    "total_results": 0,
                    "search_type": "web",
                    "provider": "brave",
                },
            )()
        )

        with patch("yams.tools.search.tool.get_search_provider", return_value=mock_provider):
            tool = create_search_tool(settings)
            result = await tool("no results")

        assert result["total_results"] == 0
        assert result["results"] == []
