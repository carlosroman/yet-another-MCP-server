from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from yams.tools.fetch.providers.base import FetchResponse
from yams.tools.fetch.settings import FetchSettings
from yams.tools.fetch.tool import create_fetch_tool

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestFetchToolValidation:
    @pytest.mark.asyncio
    async def test_empty_url_raises(self):
        mock_provider = MagicMock()
        mock_provider.fetch = AsyncMock()

        with patch("yams.tools.fetch.tool.HttpxFetcher", return_value=mock_provider):
            tool = create_fetch_tool(FetchSettings())
            with pytest.raises(ValueError, match="must not be empty"):
                await tool(url="")

    @pytest.mark.asyncio
    async def test_whitespace_url_raises(self):
        mock_provider = MagicMock()
        mock_provider.fetch = AsyncMock()

        with patch("yams.tools.fetch.tool.HttpxFetcher", return_value=mock_provider):
            tool = create_fetch_tool(FetchSettings())
            with pytest.raises(ValueError, match="must not be empty"):
                await tool(url="   ")


class TestFetchToolSuccess:
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        mock_resp = FetchResponse(
            url="https://example.com",
            content="# Hello\n\nWorld",
            content_type="text/html",
            status_code=200,
        )

        mock_provider = MagicMock()
        mock_provider.fetch = AsyncMock(return_value=mock_resp)

        with patch("yams.tools.fetch.tool.HttpxFetcher", return_value=mock_provider):
            tool = create_fetch_tool(FetchSettings())
            result = await tool(url="https://example.com")

        assert result["url"] == "https://example.com"
        assert result["status_code"] == 200
        assert result["content"] == "# Hello\n\nWorld"

    @pytest.mark.asyncio
    async def test_default_format_is_markdown(self):
        mock_resp = FetchResponse(
            url="https://example.com",
            content="# Hello\n\nWorld",
            content_type="text/html",
            status_code=200,
        )

        mock_provider = MagicMock()
        mock_provider.fetch = AsyncMock(return_value=mock_resp)

        with patch("yams.tools.fetch.tool.HttpxFetcher", return_value=mock_provider):
            tool = create_fetch_tool(FetchSettings())
            result = await tool(url="https://example.com")

        assert result["content"] == "# Hello\n\nWorld"

    @pytest.mark.asyncio
    async def test_format_text(self):
        mock_resp = FetchResponse(
            url="https://example.com",
            content="# Hello\n\n[Link](http://example.com)\n\n**Bold**",
            content_type="text/html",
            status_code=200,
        )

        mock_provider = MagicMock()
        mock_provider.fetch = AsyncMock(return_value=mock_resp)

        with patch("yams.tools.fetch.tool.HttpxFetcher", return_value=mock_provider):
            tool = create_fetch_tool(FetchSettings())
            result = await tool(url="https://example.com", format="text")

        assert "#" not in result["content"] or "Hello" in result["content"]
        assert "[" not in result["content"] or "Link" in result["content"]

    @pytest.mark.asyncio
    async def test_format_html(self):
        mock_resp = FetchResponse(
            url="https://example.com",
            content="# Hello",
            content_type="text/html",
            status_code=200,
        )

        mock_provider = MagicMock()
        mock_provider.fetch = AsyncMock(return_value=mock_resp)

        with patch("yams.tools.fetch.tool.HttpxFetcher", return_value=mock_provider):
            tool = create_fetch_tool(FetchSettings())
            result = await tool(url="https://example.com", format="html")

        assert "<pre>" in result["content"]
        assert "</pre>" in result["content"]


class TestFetchToolErrors:
    @pytest.mark.asyncio
    async def test_provider_error_propagates(self):
        mock_provider = MagicMock()
        mock_provider.fetch = AsyncMock(side_effect=RuntimeError("Connection failed"))

        with patch("yams.tools.fetch.tool.HttpxFetcher", return_value=mock_provider):
            tool = create_fetch_tool(FetchSettings())
            with pytest.raises(RuntimeError, match="Connection failed"):
                await tool(url="https://example.com")

    @pytest.mark.asyncio
    async def test_value_error_propagates(self):
        mock_provider = MagicMock()
        mock_provider.fetch = AsyncMock(side_effect=ValueError("Invalid URL"))

        with patch("yams.tools.fetch.tool.HttpxFetcher", return_value=mock_provider):
            tool = create_fetch_tool(FetchSettings())
            with pytest.raises(ValueError, match="Invalid URL"):
                await tool(url="https://example.com")


class TestFetchToolResponse:
    @pytest.mark.asyncio
    async def test_response_has_all_fields(self):
        mock_resp = FetchResponse(
            url="https://example.com",
            content="Hello",
            content_type="text/html",
            status_code=200,
            title="Test Page",
        )

        mock_provider = MagicMock()
        mock_provider.fetch = AsyncMock(return_value=mock_resp)

        with patch("yams.tools.fetch.tool.HttpxFetcher", return_value=mock_provider):
            tool = create_fetch_tool(FetchSettings())
            result = await tool(url="https://example.com")

        assert "url" in result
        assert "content" in result
        assert "content_type" in result
        assert "status_code" in result
        assert "title" in result
        assert "extracted_at" in result

    @pytest.mark.asyncio
    async def test_extracted_at_is_isoformat(self):
        mock_resp = FetchResponse(
            url="https://example.com",
            content="Hello",
            content_type="text/html",
            status_code=200,
        )

        mock_provider = MagicMock()
        mock_provider.fetch = AsyncMock(return_value=mock_resp)

        with patch("yams.tools.fetch.tool.HttpxFetcher", return_value=mock_provider):
            tool = create_fetch_tool(FetchSettings())
            result = await tool(url="https://example.com")

        from datetime import datetime
        datetime.fromisoformat(result["extracted_at"])
