from __future__ import annotations

import asyncio
import logging

from mcp.server import MCPServer

from yams.config.settings import SearchSettings
from yams.tools.search import create_search_tool

logger = logging.getLogger(__name__)


def init_server(settings: SearchSettings | None = None) -> MCPServer:
    if settings is None:
        settings = SearchSettings()

    server = MCPServer("yams")
    search_fn = create_search_tool(settings)
    server.tool(description="Search the web using Brave Search API")(search_fn)
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
