# Search Tool

The `search` tool provides web search capabilities using the Brave Search API.

## Configuration

### Environment Variables

Set the following environment variables (or add them to a `.env` file):

```bash
# Required for Brave Search provider
export BRAVE_API_KEY="your-brave-api-key-here"

# Optional configuration
export YAMS_SEARCH_PROVIDER="brave"        # "brave" or "searxng" (default: brave)
export YAMS_SEARCH_MODE="default"          # "default" or "brave_llm_context" (default: default)
export YAMS_SEARCH_COUNT=10                # Results per query (1-20, default: 10)
export YAMS_SEARCH_COUNTRY="us"            # Country code (default: us)
export YAMS_SEARCH_LANGUAGE="en"           # Language code (default: en)
export YAMS_SEARCH_LLM_CONTEXT_COUNT=20    # LLM Context results (default: 20)
export YAMS_SEARCH_LLM_CONTEXT_MAX_TOKENS=8192  # LLM Context max tokens (default: 8192)
```

### `.env` File Example

```env
BRAVE_API_KEY=your-brave-api-key-here
YAMS_SEARCH_PROVIDER=brave
YAMS_SEARCH_MODE=default
YAMS_SEARCH_COUNT=10
YAMS_SEARCH_COUNTRY=us
YAMS_SEARCH_LANGUAGE=en
YAMS_SEARCH_LLM_CONTEXT_COUNT=20
YAMS_SEARCH_LLM_CONTEXT_MAX_TOKENS=8192
```

## Usage

### Tool Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query string |
| `count` | integer | No | 10 | Number of results (1-20) |
| `search_type` | string | No | "web" | Type: "web", "news", "images", or "videos" |
| `mode` | string | No | config value | Override mode: "default" or "brave_llm_context" |

### Example Request

#### Default Mode (Brave Web Search)

```json
{
  "name": "search",
  "arguments": {
    "query": "python machine learning",
    "count": 5,
    "search_type": "web"
  }
}
```

#### LLM Context Mode (Runtime Override)

```json
{
  "name": "search",
  "arguments": {
    "query": "python machine learning",
    "count": 30,
    "search_type": "web",
    "mode": "brave_llm_context"
  }
}
```

### Example Response

```json
{
  "query": "python machine learning",
  "provider": "brave",
  "search_type": "web",
  "total_results": 5,
  "results": [
    {
      "title": "Python Machine Learning Tutorial",
      "url": "https://example.com/tutorial",
      "snippet": "Learn machine learning with Python..."
    }
  ]
}
```

## Quick Testing

### Option 1: Using the MCP Server (Integration Test)

```bash
# Set your API key
export BRAVE_API_KEY="your-api-key"

# Run the integration test
uv run pytest tests/integration/test_search_real_api.py -v

# Or run with a specific query
uv run pytest tests/integration/ -k "mocked" -v
```

### Option 2: Direct Python Test Script

Create a test script `test_search.py`:

```python
import asyncio
import os
from yams.config.settings import SearchSettings
from yams.tools.search import create_search_tool


async def main():
    settings = SearchSettings()
    search_fn = create_search_tool(settings)

    result = await search_fn(query="python programming", count=3)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
export BRAVE_API_KEY="your-api-key"
uv run python test_search.py
```

### Option 3: Using MCP Client

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_search():
    server_params = StdioServerParameters(command="uv", args=["run", "yams"])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Call search tool
            result = await session.call_tool(
                "search", arguments={"query": "hello world", "count": 3}
            )
            print(result)


asyncio.run(test_search())
```

## Search Modes

### Default Mode

Uses the Brave Web Search API (`/api/v1/search`). Supports all search types:
- `web` - Web search results
- `news` - News articles
- `images` - Image search
- `videos` - Video search

### Brave LLM Context Mode

Uses the Brave LLM Context API (`/api/v1/llm/context`). Designed for LLM grounding:
- Returns context snippets from search results
- Only supports `web` search type (raises error for news/images/videos)
- Configurable `count` (default: 20) and `max_tokens` (default: 8192)
- Snippets are joined with double newlines for better context

## Error Handling

The tool raises errors for:

- **Missing API key**: `BRAVE_API_KEY` not set when using Brave provider
- **Invalid API key**: HTTP 401 from Brave API
- **Rate limited**: HTTP 429 from Brave API
- **Network errors**: Connection timeouts or failures
- **Unsupported search type**: LLM Context mode only supports `web` search

## Getting a Brave API Key

1. Visit [Brave Search API](https://brave.com/search/api/)
2. Sign up for a free account
3. Create a new API key
4. Copy the key and set it as `BRAVE_API_KEY`

Free tier includes 2,000 queries per month.
