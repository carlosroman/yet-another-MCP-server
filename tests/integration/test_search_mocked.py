from __future__ import annotations

import json
from unittest.mock import patch

import httpx
import pytest

from yams.config.settings import SearchSettings
from yams.server import init_server


class TestSearchMocked:
    @pytest.mark.asyncio
    async def test_search_with_mocked_brave_api(self):
        mock_body = {
            "web": {
                "results": [
                    {
                        "title": "Google",
                        "url": "https://www.google.com",
                        "description": "Search Google",
                    }
                ]
            }
        }

        transport = httpx.MockTransport(
            lambda request: httpx.Response(200, json=mock_body)
        )

        settings = SearchSettings(provider="brave", brave_api_key="test-key")
        server = init_server(settings)

        with patch("httpx.AsyncClient", return_value=httpx.AsyncClient(transport=transport)):
            result = await server.call_tool("websearch", {"query": "google"})

        parsed = json.loads(result.content[0].text)
        assert parsed["query"] == "google"
        assert parsed["provider"] == "brave"
        assert parsed["total_results"] == 1
        assert parsed["results"][0]["url"] == "https://www.google.com"
