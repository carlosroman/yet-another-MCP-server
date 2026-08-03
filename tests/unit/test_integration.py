from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from yams.config.settings import SearchSettings
from yams.server import init_server


class TestIntegrationSearchFlow:
    @pytest.mark.asyncio
    async def test_full_search_flow(self):
        settings = SearchSettings(
            provider="brave",
            brave_api_key="test-key",
        )

        mock_result = type(
            "MockResult",
            (),
            {
                "title": "MCP Server",
                "url": "https://example.com",
                "snippet": "A MCP server",
                "score": 0.9,
            },
        )()

        mock_response = type(
            "MockResponse",
            (),
            {
                "query": "python mcp",
                "results": [mock_result],
                "total_results": 1,
                "search_type": "web",
                "provider": "brave",
            },
        )()

        mock_provider = AsyncMock()
        mock_provider.search = AsyncMock(return_value=mock_response)

        with patch("yams.tools.search.tool.get_search_provider", return_value=mock_provider):
            server = init_server(settings)
            await server.list_tools()

            result = await server.call_tool("websearch", {"query": "python mcp"})

        parsed = json.loads(result.content[0].text)
        assert parsed["query"] == "python mcp"
        assert parsed["total_results"] == 1
        assert parsed["provider"] == "brave"

    @pytest.mark.asyncio
    async def test_error_flow(self):
        settings = SearchSettings(
            provider="brave",
            brave_api_key="test-key",
        )

        mock_provider = AsyncMock()
        mock_provider.search = AsyncMock(side_effect=RuntimeError("API failure"))

        with patch("yams.tools.search.tool.get_search_provider", return_value=mock_provider):
            server = init_server(settings)

            with pytest.raises(Exception, match="API failure"):
                await server.call_tool("websearch", {"query": "test"})

    def test_provider_switching(self):
        brave_settings = SearchSettings(provider="brave", brave_api_key="key")
        server = init_server(brave_settings)
        assert server.name == "yams"

        searxng_settings = SearchSettings(provider="searxng", brave_api_key="")
        server2 = init_server(searxng_settings)
        assert server2.name == "yams"
