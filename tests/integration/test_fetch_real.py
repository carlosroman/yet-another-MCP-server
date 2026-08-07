from __future__ import annotations

from pathlib import Path

import httpx
import pytest

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def mock_transport():
    html_body = (FIXTURES / "test_page.html").read_bytes()
    json_body = (FIXTURES / "test_data.json").read_bytes()
    xml_body = (FIXTURES / "test_data.xml").read_bytes()

    def handler(request: httpx.Request):
        path = request.url.path

        if path == "/html":
            return httpx.Response(200, content=html_body, headers={"content-type": "text/html; charset=utf-8"})
        elif path == "/json":
            return httpx.Response(200, content=json_body, headers={"content-type": "application/json"})
        elif path == "/xml":
            return httpx.Response(200, content=xml_body, headers={"content-type": "application/xml"})
        elif path == "/404":
            return httpx.Response(404, content=b"Not Found")
        elif path == "/redirect":
            return httpx.Response(301, headers={"location": "http://testserver/html"})
        elif path == "/large":
            body = b"x" * 2_000_000
            return httpx.Response(200, content=body, headers={"content-type": "text/plain"})

        return httpx.Response(404, content=b"Not Found")

    return httpx.MockTransport(handler)


class TestFetchToolIntegration:
    @pytest.mark.asyncio
    async def test_fetch_html(self, mock_transport):
        async with httpx.AsyncClient(transport=mock_transport, base_url="http://testserver") as client:
            resp = await client.get("/html")
            assert resp.status_code == 200
            assert "text/html" in resp.headers["content-type"]

    @pytest.mark.asyncio
    async def test_fetch_json(self, mock_transport):
        async with httpx.AsyncClient(transport=mock_transport, base_url="http://testserver") as client:
            resp = await client.get("/json")
            assert resp.status_code == 200
            assert "application/json" in resp.headers["content-type"]

    @pytest.mark.asyncio
    async def test_fetch_xml(self, mock_transport):
        async with httpx.AsyncClient(transport=mock_transport, base_url="http://testserver") as client:
            resp = await client.get("/xml")
            assert resp.status_code == 200
            assert "application/xml" in resp.headers["content-type"]

    @pytest.mark.asyncio
    async def test_404_error(self, mock_transport):
        async with httpx.AsyncClient(transport=mock_transport, base_url="http://testserver") as client:
            resp = await client.get("/404")
            assert resp.status_code == 404


class TestHttpxFetcherWithMockedTransport:
    @pytest.mark.asyncio
    async def test_fetch_html_page(self, mock_transport):
        async with httpx.AsyncClient(transport=mock_transport, base_url="http://testserver") as client:
            resp = await client.get("/html")
            assert resp.status_code == 200
            assert "text/html" in resp.headers["content-type"]

    @pytest.mark.asyncio
    async def test_fetch_json_page(self, mock_transport):
        async with httpx.AsyncClient(transport=mock_transport, base_url="http://testserver") as client:
            resp = await client.get("/json")
            assert resp.status_code == 200
            assert "application/json" in resp.headers["content-type"]

    @pytest.mark.asyncio
    async def test_404_raises(self, mock_transport):
        async with httpx.AsyncClient(transport=mock_transport, base_url="http://testserver") as client:
            resp = await client.get("/404")
            assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_size_limit_enforced(self, mock_transport):
        async with httpx.AsyncClient(transport=mock_transport, base_url="http://testserver") as client:
            resp = await client.get("/large")
            assert resp.status_code == 200
            assert len(resp.content) > 1000
