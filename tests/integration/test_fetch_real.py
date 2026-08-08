from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from yams.tools.fetch.providers.scrapling_fetcher import ScraplingFetcher
from yams.tools.fetch.settings import FetchSettings

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def test_server():
    html_body = (FIXTURES / "test_page.html").read_bytes()
    json_body = (FIXTURES / "test_data.json").read_bytes()
    xml_body = (FIXTURES / "test_data.xml").read_bytes()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/html":
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html_body)
            elif self.path == "/json":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json_body)
            elif self.path == "/xml":
                self.send_response(200)
                self.send_header("Content-Type", "application/xml")
                self.end_headers()
                self.wfile.write(xml_body)
            elif self.path == "/404":
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Not Found")
            elif self.path == "/redirect":
                self.send_response(301)
                self.send_header("Location", f"http://127.0.0.1:{test_server.server_port}/html")
                self.end_headers()
            elif self.path == "/large":
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"x" * 2_000_000)
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Not Found")

        def log_message(self, format, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    yield f"http://127.0.0.1:{server.server_port}"

    server.shutdown()


class TestScraplingFetcherIntegration:
    @pytest.mark.asyncio
    async def test_fetch_html_page(self, test_server):
        settings = FetchSettings()
        fetcher = ScraplingFetcher(settings)
        result = await fetcher.fetch(f"{test_server}/html")

        assert result.status_code == 200
        assert "text/html" in result.content_type

    @pytest.mark.asyncio
    async def test_fetch_json_page(self, test_server):
        settings = FetchSettings()
        fetcher = ScraplingFetcher(settings)
        result = await fetcher.fetch(f"{test_server}/json")

        assert result.status_code == 200
        assert "application/json" in result.content_type
        assert "```json" in result.content

    @pytest.mark.asyncio
    async def test_fetch_xml_page(self, test_server):
        settings = FetchSettings()
        fetcher = ScraplingFetcher(settings)
        result = await fetcher.fetch(f"{test_server}/xml")

        assert result.status_code == 200
        assert "application/xml" in result.content_type

    @pytest.mark.asyncio
    async def test_404_raises(self, test_server):
        settings = FetchSettings()
        fetcher = ScraplingFetcher(settings)

        with pytest.raises(RuntimeError, match="HTTP 404"):
            await fetcher.fetch(f"{test_server}/404")

    @pytest.mark.asyncio
    async def test_size_limit_enforced(self, test_server):
        settings = FetchSettings(max_size=100)
        fetcher = ScraplingFetcher(settings)

        with pytest.raises(RuntimeError, match="exceeds limit"):
            await fetcher.fetch(f"{test_server}/large")
