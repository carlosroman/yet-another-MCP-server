from __future__ import annotations

from urllib.parse import urlparse

from scrapling.fetchers import AsyncFetcher

from yams.tools.fetch.providers.base import Fetcher, FetchResponse
from yams.tools.fetch.providers.converters.markitdown import MarkItDownConverter
from yams.tools.fetch.providers.converters.trafilatura import TrafilaturaConverter
from yams.tools.fetch.settings import FetchSettings


class ScraplingFetcher(Fetcher):
    def __init__(self, settings: FetchSettings):
        self._settings = settings
        self._trafilatura = TrafilaturaConverter()
        self._markitdown = MarkItDownConverter()

    async def fetch(
        self, url: str, user_agent: str | None = None, stealthy_headers: bool | None = None
    ) -> FetchResponse:
        _validate_url(url)

        effective_user_agent = user_agent or self._settings.user_agent
        effective_stealthy = (
            stealthy_headers if stealthy_headers is not None else self._settings.stealthy_headers
        )

        headers = {"User-Agent": effective_user_agent}

        try:
            resp = await AsyncFetcher.get(
                url,
                timeout=self._settings.timeout,
                follow_redirects=self._settings.follow_redirects,
                headers=headers,
                stealthy_headers=effective_stealthy,
                impersonate=self._settings.impersonate,
            )
        except (OSError, ValueError) as e:
            raise RuntimeError(f"Failed to fetch {url}: {e}")

        if resp.status >= 400:
            raise RuntimeError(f"HTTP {resp.status} fetching {url}")

        final_url = str(resp.url)
        content_type = resp.headers.get("content-type", "application/octet-stream")
        raw_body = resp.body

        size = len(raw_body) if isinstance(raw_body, bytes) else len(raw_body.encode())
        if size > self._settings.max_size:
            raise RuntimeError(f"Content size {size} exceeds limit {self._settings.max_size}")

        title = ""
        converted = self._convert(raw_body, content_type)

        return FetchResponse(
            url=final_url,
            content=converted,
            content_type=content_type,
            status_code=resp.status,
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
