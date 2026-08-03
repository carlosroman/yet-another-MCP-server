from __future__ import annotations

import json
import os

import pytest

from yams.config.settings import SearchSettings
from yams.server import init_server


class TestSearchRealAPI:
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("BRAVE_API_KEY"),
        reason="BRAVE_API_KEY environment variable not set",
    )
    async def test_search_with_real_brave_api(self):
        settings = SearchSettings(
            provider="brave",
            brave_api_key=os.environ["BRAVE_API_KEY"],
        )
        server = init_server(settings)

        result = await server.call_tool("search", {"query": "google"})
        parsed = json.loads(result.content[0].text)

        assert parsed["query"] == "google"
        assert parsed["provider"] == "brave"
        assert parsed["total_results"] > 0
        assert "google.com" in parsed["results"][0]["url"]
