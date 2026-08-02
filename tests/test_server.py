from __future__ import annotations

from unittest.mock import patch

import pytest

from yams.config.settings import SearchSettings
from yams.server import init_server


class TestInitServer:
    def test_returns_server(self):
        settings = SearchSettings(provider="searxng", brave_api_key="")
        server = init_server(settings)
        assert server is not None

    def test_server_name(self):
        settings = SearchSettings(provider="searxng", brave_api_key="")
        server = init_server(settings)
        assert server.name == "yams"

    @pytest.mark.asyncio
    async def test_tool_registered(self):
        settings = SearchSettings(provider="searxng", brave_api_key="")
        server = init_server(settings)
        tools = await server.list_tools()
        tool_names = [t.name for t in tools]
        assert "search" in tool_names

    def test_default_settings(self):
        with patch.dict("os.environ", {"YAMS_SEARCH_PROVIDER": "searxng"}):
            server = init_server()
            assert server.name == "yams"
