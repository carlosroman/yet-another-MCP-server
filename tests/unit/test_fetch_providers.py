from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from yams.tools.fetch.providers.base import ContentConverter, Fetcher, FetchResponse
from yams.tools.fetch.providers.converters.trafilatura import TrafilaturaConverter
from yams.tools.fetch.providers.scrapling_fetcher import ScraplingFetcher
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


class TestScraplingFetcherURLValidation:
    @pytest.mark.asyncio
    async def test_empty_url_raises(self):
        settings = FetchSettings()
        fetcher = ScraplingFetcher(settings)
        with pytest.raises(ValueError, match="must not be empty"):
            await fetcher.fetch("")

    @pytest.mark.asyncio
    async def test_invalid_scheme_raises(self):
        settings = FetchSettings()
        fetcher = ScraplingFetcher(settings)
        with pytest.raises(ValueError, match="Invalid URL scheme"):
            await fetcher.fetch("ftp://example.com")

    @pytest.mark.asyncio
    async def test_missing_hostname_raises(self):
        settings = FetchSettings()
        fetcher = ScraplingFetcher(settings)
        with pytest.raises(ValueError, match="missing hostname"):
            await fetcher.fetch("http://")


@pytest.fixture
def mock_scrapling_response():
    def _create(
        status=200, content=b"<html><body><h1>Hello</h1></body></html>", content_type="text/html"
    ):
        resp = MagicMock()
        resp.status = status
        resp.body = content
        resp.url = "https://example.com"
        resp.headers = {"content-type": content_type}
        return resp

    return _create


class TestScraplingFetcherErrors:
    @pytest.mark.asyncio
    async def test_fetch_error(self):
        settings = FetchSettings(timeout=5)
        fetcher = ScraplingFetcher(settings)

        with (
            patch(
                "yams.tools.fetch.providers.scrapling_fetcher.AsyncFetcher.get",
                new_callable=AsyncMock,
                side_effect=OSError("connection error"),
            ),
            pytest.raises(RuntimeError, match="Failed to fetch"),
        ):
            await fetcher.fetch("https://example.com")


class TestScraplingFetcherSizeLimit:
    @pytest.mark.asyncio
    async def test_size_exceeded(self, mock_scrapling_response):
        settings = FetchSettings(max_size=100)
        fetcher = ScraplingFetcher(settings)

        resp = mock_scrapling_response(content=b"x" * 200)
        with (
            patch(
                "yams.tools.fetch.providers.scrapling_fetcher.AsyncFetcher.get",
                new_callable=AsyncMock,
                return_value=resp,
            ),
            pytest.raises(RuntimeError, match="exceeds limit"),
        ):
            await fetcher.fetch("https://example.com")


class TestScraplingFetcherSuccess:
    @pytest.mark.asyncio
    async def test_successful_fetch(self, mock_scrapling_response):
        settings = FetchSettings()
        fetcher = ScraplingFetcher(settings)

        resp = mock_scrapling_response()
        with patch(
            "yams.tools.fetch.providers.scrapling_fetcher.AsyncFetcher.get",
            new_callable=AsyncMock,
            return_value=resp,
        ):
            result = await fetcher.fetch("https://example.com")

        assert isinstance(result, FetchResponse)
        assert result.url == "https://example.com"
        assert result.status_code == 200
        assert result.content_type == "text/html"

    @pytest.mark.asyncio
    async def test_404_raises(self, mock_scrapling_response):
        settings = FetchSettings()
        fetcher = ScraplingFetcher(settings)

        resp = mock_scrapling_response(status=404, content=b"Not Found")
        with (
            patch(
                "yams.tools.fetch.providers.scrapling_fetcher.AsyncFetcher.get",
                new_callable=AsyncMock,
                return_value=resp,
            ),
            pytest.raises(RuntimeError, match="HTTP 404"),
        ):
            await fetcher.fetch("https://example.com")

    @pytest.mark.asyncio
    async def test_json_content(self, mock_scrapling_response):
        settings = FetchSettings()
        fetcher = ScraplingFetcher(settings)

        json_body = b'{"key": "value"}'
        resp = mock_scrapling_response(content=json_body, content_type="application/json")
        with patch(
            "yams.tools.fetch.providers.scrapling_fetcher.AsyncFetcher.get",
            new_callable=AsyncMock,
            return_value=resp,
        ):
            result = await fetcher.fetch("https://example.com")

        assert "```json" in result.content

    @pytest.mark.asyncio
    async def test_stealthy_headers_passed(self, mock_scrapling_response):
        settings = FetchSettings()
        fetcher = ScraplingFetcher(settings)

        resp = mock_scrapling_response()
        mock_get = AsyncMock(return_value=resp)
        with patch("yams.tools.fetch.providers.scrapling_fetcher.AsyncFetcher.get", mock_get):
            await fetcher.fetch("https://example.com", stealthy_headers=True)

        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["stealthy_headers"] is True
