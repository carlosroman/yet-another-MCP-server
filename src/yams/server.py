from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from yams.config.settings import SearchSettings
from yams.tools.search import create_search_tool

logger = logging.getLogger(__name__)


def init_server(settings: SearchSettings | None = None) -> MCPServer:
    if settings is None:
        settings = SearchSettings()

    server = MCPServer("yams")
    search_fn = create_search_tool(settings)
    current_year = datetime.now(tz=UTC).year
    mode_label = "brave_llm_context (Brave LLM Context)" if settings.mode == "brave_llm_context" else "default (Brave Web Search)"
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
            f"Supports web, news, image, and video search. "
            f"Use this for current information beyond knowledge cutoff. "
            f"The current year is {current_year}. Use this year when searching for recent information or current events. "
            f"Mode: 'default' uses standard Brave Web Search (titles, URLs, snippets). "
            f"'brave_llm_context' uses Brave's LLM Context API for enhanced context with more detailed snippets - better for complex research queries."
        ))(search_fn)
    return server


def run():
    settings = SearchSettings()
    server = init_server(settings)
    logging.basicConfig(level=logging.INFO)
    logger.info("YAMS server started")

    try:
        asyncio.run(server.run_stdio_async())
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
