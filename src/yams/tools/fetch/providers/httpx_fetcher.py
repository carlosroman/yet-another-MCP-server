from __future__ import annotations

from urllib.parse import urlparse

import httpx

from yams.tools.fetch.providers.base import Fetcher, FetchResponse
from yams.tools.fetch.providers.converters.markitdown import MarkItDownConverter
from yams.tools.fetch.providers.converters.trafilatura import TrafilaturaConverter
from yams.tools.fetch.settings import FetchSettings


class HttpxFetcher(Fetcher):
    def __init__(self, settings: FetchSettings):
        self._settings = settings
        self._trafilatura = TrafilaturaConverter()
        self._markitdown = MarkItDownConverter()

    async def fetch(self, url: str, user_agent: str | None = None) -> FetchResponse:
        _validate_url(url)

        effective_user_agent = user_agent or self._settings.user_agent

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self._settings.timeout),
            follow_redirects=self._settings.follow_redirects,
            headers={"User-Agent": effective_user_agent},
        ) as client:
            try:
                resp = await client.get(url)
            except httpx.TimeoutException:
                raise RuntimeError(f"Fetch timed out after {self._settings.timeout}s: {url}")
            except httpx.HTTPError as e:
                raise RuntimeError(f"Failed to fetch {url}: {e}")

        if resp.status_code >= 400:
            raise RuntimeError(f"HTTP {resp.status_code} fetching {url}")

        final_url = str(resp.url)
        content_type = resp.headers.get("content-type", "application/octet-stream")
        raw_body = resp.content

        size = len(raw_body)
        if size > self._settings.max_size:
            raise RuntimeError(f"Content size {size} exceeds limit {self._settings.max_size}")

        title = ""
        converted = self._convert(raw_body, content_type)

        return FetchResponse(
            url=final_url,
            content=converted,
            content_type=content_type,
            status_code=resp.status_code,
            title=title,
        )

    def _convert(self, content: bytes | str, content_type: str) -> str:
        ct = content_type.lower()
        if "pdf" in ct:
            return self._markitdown.convert(content, content_type)
        return self._trafilatura.convert(content, content_type)


def _validate_url(url: str) -> None:
    if not url or not url.strip():
        raise ValueError("URL must not be empty")

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Invalid URL scheme '{parsed.scheme}'. Only http/https are supported.")
    if not parsed.hostname:
        raise ValueError(f"Invalid URL: missing hostname in '{url}'")
