from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from yams.config.settings import SearchSettings
from yams.tools.fetch import FetchSettings, create_fetch_tool
from yams.tools.search import create_search_tool

logger = logging.getLogger(__name__)


def init_server(
    search_settings: SearchSettings | None = None,
    fetch_settings: FetchSettings | None = None,
) -> MCPServer:
    if search_settings is None:
        search_settings = SearchSettings()

    server = MCPServer("yams")
    search_fn = create_search_tool(search_settings)
    current_year = datetime.now(tz=UTC).year
    server.tool(
        name="websearch",
        title="Web Search",
        annotations=ToolAnnotations(
            read_only_hint=True,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=True,
        ),
        description=(
            f"Search the public web for information. "
            f"Use this for current information beyond knowledge cutoff. "
            f"The current year is {current_year}. Use this year when searching for recent information or current events. "
            f"Search types: 'web' for general info, 'news' for recent events/sports/results, 'images' for photos, 'videos' for video content. "
            f"Mode: 'default' uses standard Brave Web Search (titles, URLs, snippets). "
            f"'brave_llm_context' uses Brave's LLM Context API for enhanced context with more detailed snippets - better for complex research queries."
        ),
    )(search_fn)

    fetch_fn = create_fetch_tool(fetch_settings or FetchSettings())
    server.tool(
        name="webfetch",
        title="Fetch Web Page",
        annotations=ToolAnnotations(
            read_only_hint=True,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=True,
        ),
        description=(
            "Fetch content from an HTTP or HTTPS URL and return it as text, markdown, or HTML. Markdown is the default. "
            "Use this to read the full content of web pages found via search or provided by the user. "
            "Supports HTML, JSON, XML, and PDF content types. "
        ),
    )(fetch_fn)

    return server


def run():
    search_settings = SearchSettings()
    server = init_server(search_settings)
    logging.basicConfig(level=logging.INFO)
    logger.info("YAMS server started")

    try:
        asyncio.run(server.run_stdio_async())
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
