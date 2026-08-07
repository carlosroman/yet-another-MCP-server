from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from yams.tools.fetch.providers.base import ContentConverter, Fetcher, FetchResponse
from yams.tools.fetch.providers.converters.trafilatura import TrafilaturaConverter
from yams.tools.fetch.providers.httpx_fetcher import HttpxFetcher
from yams.tools.fetch.settings import FetchSettings

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestFetchResponse:
    def test_create_response(self):
        r = FetchResponse(
            url="https://example.com",
            content="<html></html>",
            content_type="text/html",
            status_code=200,
        )
        assert r.url == "https://example.com"
        assert r.status_code == 200
        assert r.title is None
        assert r.metadata == {}
        assert r.extracted_at is not None


class TestFetcherABC:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            Fetcher()  # type: ignore

    def test_must_implement_fetch(self):
        class Incomplete(Fetcher):
            pass

        with pytest.raises(TypeError):
            Incomplete()


class TestContentConverterABC:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            ContentConverter()  # type: ignore

    def test_must_implement_convert(self):
        class Incomplete(ContentConverter):
            pass

        with pytest.raises(TypeError):
            Incomplete()


class TestTrafilaturaConverter:
    @pytest.fixture
    def converter(self):
        return TrafilaturaConverter()

    def test_html_conversion(self, converter):
        html = "<html><body><h1>Hello</h1><p>World</p></body></html>"
        result = converter.convert(html, "text/html")
        assert isinstance(result, str)

    def test_empty_content(self, converter):
        assert converter.convert("", "text/html") == ""

    def test_none_content(self, converter):
        assert converter.convert(None, "text/html") == ""  # type: ignore

    def test_json_conversion(self, converter):
        data = {"key": "value", "num": 42}
        result = converter.convert(json.dumps(data), "application/json")
        assert "```json" in result
        assert '"key": "value"' in result

    def test_json_bytes_conversion(self, converter):
        data = b'{"key": "value"}'
        result = converter.convert(data, "application/json")
        assert "```json" in result

    def test_invalid_json_fallback(self, converter):
        result = converter.convert("not json", "application/json")
        assert result == "not json"

    def test_fixture_html(self, converter):
        html = (FIXTURES / "test_page.html").read_text()
        result = converter.convert(html, "text/html")
        assert isinstance(result, str)

    def test_fixture_json(self, converter):
        data = (FIXTURES / "test_data.json").read_text()
        result = converter.convert(data, "application/json")
        assert "```json" in result
        assert "alpha" in result


class TestHttpxFetcherURLValidation:
    @pytest.mark.asyncio
    async def test_empty_url_raises(self):
        settings = FetchSettings()
        fetcher = HttpxFetcher(settings)
        with pytest.raises(ValueError, match="must not be empty"):
            await fetcher.fetch("")

    @pytest.mark.asyncio
    async def test_invalid_scheme_raises(self):
        settings = FetchSettings()
        fetcher = HttpxFetcher(settings)
        with pytest.raises(ValueError, match="Invalid URL scheme"):
            await fetcher.fetch("ftp://example.com")

    @pytest.mark.asyncio
    async def test_missing_hostname_raises(self):
        settings = FetchSettings()
        fetcher = HttpxFetcher(settings)
        with pytest.raises(ValueError, match="missing hostname"):
            await fetcher.fetch("http://")


@pytest.fixture
def mock_httpx_response():
    def _create(status_code=200, content=b"<html><body><h1>Hello</h1></body></html>", content_type="text/html"):
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = status_code
        resp.content = content
        resp.url = httpx.URL("https://example.com")
        resp.headers = httpx.Headers({"content-type": content_type})
        return resp
    return _create


class TestHttpxFetcherErrors:
    @pytest.mark.asyncio
    async def test_timeout_error(self):
        settings = FetchSettings(timeout=5)
        fetcher = HttpxFetcher(settings)

        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("yams.tools.fetch.providers.httpx_fetcher.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(RuntimeError, match="timed out"),
        ):
            await fetcher.fetch("https://example.com")


class TestHttpxFetcherSizeLimit:
    @pytest.mark.asyncio
    async def test_size_exceeded(self):
        settings = FetchSettings(max_size=100)
        fetcher = HttpxFetcher(settings)

        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 200
        resp.content = b"x" * 200
        resp.url = httpx.URL("https://example.com")
        resp.headers = {"content-type": "text/html"}

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("yams.tools.fetch.providers.httpx_fetcher.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(RuntimeError, match="exceeds limit"),
        ):
            await fetcher.fetch("https://example.com")


class TestHttpxFetcherSuccess:
    @pytest.mark.asyncio
    async def test_successful_fetch(self, mock_httpx_response):
        settings = FetchSettings()
        fetcher = HttpxFetcher(settings)

        resp = mock_httpx_response()
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("yams.tools.fetch.providers.httpx_fetcher.httpx.AsyncClient", return_value=mock_client):
            result = await fetcher.fetch("https://example.com")

        assert isinstance(result, FetchResponse)
        assert result.url == "https://example.com"
        assert result.status_code == 200
        assert result.content_type == "text/html"

    @pytest.mark.asyncio
    async def test_404_raises(self, mock_httpx_response):
        settings = FetchSettings()
        fetcher = HttpxFetcher(settings)

        resp = mock_httpx_response(status_code=404, content=b"Not Found")
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("yams.tools.fetch.providers.httpx_fetcher.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(RuntimeError, match="HTTP 404"),
        ):
            await fetcher.fetch("https://example.com")

    @pytest.mark.asyncio
    async def test_json_content(self, mock_httpx_response):
        settings = FetchSettings()
        fetcher = HttpxFetcher(settings)

        json_body = b'{"key": "value"}'
        resp = mock_httpx_response(content=json_body, content_type="application/json")
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("yams.tools.fetch.providers.httpx_fetcher.httpx.AsyncClient", return_value=mock_client):
            result = await fetcher.fetch("https://example.com")

        assert "```json" in result.content
