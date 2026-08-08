from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from yams.config.settings import SearchSettings
from yams.server import init_server


def create_mock_response(status_code: int, json_data: dict | None = None, text: str = ""):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data or {}
    mock_resp.text = text
    return mock_resp


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

        mock_response = create_mock_response(200, mock_body)

        async def mock_get(*args, **kwargs):
            return mock_response

        settings = SearchSettings(provider="brave", brave_api_key="test-key")
        server = init_server(settings)

        with patch("curl_cffi.requests.AsyncSession.get", new=mock_get):
            result = await server.call_tool("websearch", {"query": "google"})

        parsed = json.loads(result.content[0].text)
        assert parsed["query"] == "google"
        assert parsed["provider"] == "brave"
        assert parsed["total_results"] == 1
        assert parsed["results"][0]["url"] == "https://www.google.com"

    @pytest.mark.asyncio
    async def test_search_brave_llm_context_mode(self):
        mock_body = {
            "grounding": {
                "generic": [
                    {
                        "title": "Python Async",
                        "url": "https://docs.python.org/3/library/asyncio.html",
                        "description": "Asyncio documentation",
                    }
                ]
            }
        }

        mock_response = create_mock_response(200, mock_body)

        async def mock_get(*args, **kwargs):
            return mock_response

        settings = SearchSettings(
            provider="brave",
            mode="brave_llm_context",
            brave_api_key="test-key",
        )
        server = init_server(settings)

        with patch("curl_cffi.requests.AsyncSession.get", new=mock_get):
            result = await server.call_tool("websearch", {"query": "python async"})

        parsed = json.loads(result.content[0].text)
        assert parsed["query"] == "python async"
        assert parsed["provider"] == "brave_llm_context"
        assert parsed["total_results"] == 1
        assert parsed["results"][0]["url"] == "https://docs.python.org/3/library/asyncio.html"

    @pytest.mark.asyncio
    async def test_search_mode_override_at_call_time(self):
        mock_body = {
            "grounding": {
                "generic": [
                    {
                        "title": "Override Result",
                        "url": "https://example.com/override",
                        "description": "Mode override test",
                    }
                ]
            }
        }

        mock_response = create_mock_response(200, mock_body)

        async def mock_get(*args, **kwargs):
            return mock_response

        settings = SearchSettings(
            provider="brave",
            mode="default",
            brave_api_key="test-key",
        )
        server = init_server(settings)

        with patch("curl_cffi.requests.AsyncSession.get", new=mock_get):
            result = await server.call_tool(
                "websearch",
                {"query": "test", "mode": "brave_llm_context"},
            )

        parsed = json.loads(result.content[0].text)
        assert parsed["query"] == "test"
        assert parsed["provider"] == "brave_llm_context"
        assert parsed["total_results"] == 1
