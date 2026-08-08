from __future__ import annotations

import re
from typing import Literal

from yams.tools.fetch.providers.base import FetchResponse
from yams.tools.fetch.providers.scrapling_fetcher import ScraplingFetcher
from yams.tools.fetch.settings import FetchSettings


def create_fetch_tool(settings: FetchSettings | None = None):
    if settings is None:
        settings = FetchSettings()

    provider = ScraplingFetcher(settings)

    async def webfetch(
        url: str,
        format: Literal["markdown", "text", "html"] = "markdown",
        user_agent: str | None = None,
        stealthy_headers: bool | None = None,
    ) -> dict:
        if not url or not url.strip():
            raise ValueError("URL must not be empty")

        response = await provider.fetch(
            url, user_agent=user_agent, stealthy_headers=stealthy_headers
        )
        content = _format_content(response, format)

        return {
            "url": response.url,
            "content": content,
            "content_type": response.content_type,
            "status_code": response.status_code,
            "title": response.title,
            "extracted_at": response.extracted_at.isoformat(),
        }

    return webfetch


def _format_content(response: FetchResponse, fmt: str) -> str:
    if fmt == "text":
        text = re.sub(r"#+ ", "", response.content)
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        text = re.sub(r"[*_~`]", "", text)
        text = re.sub(r"!\[([^\]]*)\]\([^\)]+\)", r"[IMAGE: \1]", text)
        return text.strip()
    elif fmt == "html":
        return f"<pre>{response.content}</pre>"
    return response.content
