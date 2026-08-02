# Search Tool Implementation Plan

## Overview

Implement the `search` tool for YAMS (Yet Another MCP Server) with Brave Search API as the default provider, designed to replace web search functionality in Opencode/Claude Code.

## Requirements

1. **Single `search` tool** with `search_type` parameter (web, news, images, videos)
2. **Environment variable configuration** with `.env` file override support
3. **Formatted results** optimized for agent consumption
4. **Return errors to agent** (validation errors, API errors)
5. **Async implementation** using httpx
6. **Provider abstraction** for easy addition of SearXNG and other providers
7. **Unit tests** written alongside implementation

## Architecture

### Directory Structure

```
src/yams/
├── __init__.py
├── __main__.py
├── server.py
├── config/
│   ├── __init__.py
│   └── settings.py
└── tools/
    ├── __init__.py
    ├── search.py
    └── search/
        ├── __init__.py
        └── providers/
            ├── __init__.py
            ├── base.py
            └── brave.py

tests/
├── __init__.py
├── test_config.py
├── test_search_providers.py
├── test_search_tool.py
├── test_server.py
└── test_integration.py
```

### Tool Signature

```python
search(
    query: str,           # Required search terms
    count: int = 10,      # Number of results (1-20)
    search_type: str = "web"  # "web" | "news" | "images" | "videos"
)
```

### Configuration

**Environment Variables:**

```bash
# Required
YAMS_SEARCH_PROVIDER=brave          # "brave" | "searxng"
BRAVE_API_KEY=your_key_here         # For Brave provider

# Optional
YAMS_SEARCH_COUNT=10                # Default results count
YAMS_SEARCH_COUNTRY=us              # Default country code
YAMS_SEARCH_LANGUAGE=en             # Default language

# SearXNG (when provider = searxng)
SEARXNG_BASE_URL=http://localhost:8080
```

### Response Format

```json
{
  "query": "python async http client",
  "results": [
    {
      "title": "Async HTTP Client Libraries in Python",
      "url": "https://example.com",
      "snippet": "Brief description...",
      "score": 0.95
    }
  ],
  "total_results": 10,
  "search_type": "web",
  "provider": "brave"
}
```

## Dependencies

```toml
[project.dependencies]
mcp = ">=1.0.0"
httpx = ">=0.27.0"
pydantic = ">=2.0.0"
python-dotenv = ">=1.0.0"

[dependency-groups.test]
pytest = ">=8.0.0"
pytest-asyncio = ">=0.23.0"

[dependency-groups.lint]
ruff = ">=0.6.0"
```

## Implementation Phases

### Phase 1: Project Structure & Dependencies

**Files:**
- `pyproject.toml` - Add dependencies and entry points
- `src/yams/__init__.py` - Package init
- `src/yams/__main__.py` - CLI entrypoint

**Tests:** None (setup only)

### Phase 2: Configuration Layer

**Files:**
- `src/yams/config/__init__.py`
- `src/yams/config/settings.py` - Pydantic Settings with env var support

**Features:**
- Load from `.env` file if present
- Validate required settings
- Provider-agnostic config interface

**Tests:**
- `tests/test_config.py`
  - Env var loading
  - `.env` file parsing
  - Validation errors
  - Provider-specific config

### Phase 3: Provider Abstraction

**Files:**
- `src/yams/tools/search/providers/__init__.py`
- `src/yams/tools/search/providers/base.py` - ABC and models

**Features:**
- `SearchProvider` ABC with `search()` method
- `SearchResult` Pydantic model
- `SearchResponse` Pydantic model
- Factory function `get_search_provider()`

**Tests:**
- `tests/test_search_providers.py`
  - ABC enforcement
  - Interface contract
  - Factory function

### Phase 4: Brave Provider

**Files:**
- `src/yams/tools/search/providers/brave.py`

**Features:**
- `BraveSearchProvider` implementation
- Async HTTP client using httpx
- Map Brave API response to `SearchResponse`
- Handle Brave-specific params (country, language, freshness)
- Error handling (API errors, rate limits)

**Tests:**
- `tests/test_search_providers.py` (continued)
  - API response parsing
  - Error handling
  - Parameter mapping
  - Mocked API calls

### Phase 5: Search Tool

**Files:**
- `src/yams/tools/__init__.py`
- `src/yams/tools/search.py`

**Features:**
- MCP tool definition
- Parameter validation
- Provider routing
- Formatted response construction
- Error handling wrapper

**Tests:**
- `tests/test_search_tool.py`
  - Parameter validation
  - Response formatting
  - Error propagation
  - Provider selection

### Phase 6: Server Integration

**Files:**
- `src/yams/server.py`

**Features:**
- Initialize MCP server
- Register `search` tool
- Load configuration
- Startup/shutdown hooks

**Tests:**
- `tests/test_server.py`
  - Tool registration
  - MCP protocol compliance

### Phase 7: CLI Entry Point

**Files:**
- `main.py` - Update existing file
- `pyproject.toml` - Add console script entrypoint

**Features:**
- Simple wrapper that imports and runs server

**Tests:** None (integration tested)

### Phase 8: Integration Tests

**Files:**
- `tests/test_integration.py`

**Features:**
- End-to-end search flow
- Provider switching
- Error scenarios

## Test Strategy

### Patterns

- Use `pytest-asyncio` for async tests
- Mock `httpx` calls with `httpx.MockTransport`
- Test edge cases: empty results, API errors, invalid params
- No external dependencies in unit tests (all mocked)

### Coverage Goals

- Config: 100% (validation is critical)
- Provider base: 100% (interface contract)
- Brave provider: 80%+ (API integration)
- Search tool: 90%+ (core functionality)
- Server: 70%+ (integration focus)

## Future Enhancements

- SearXNG provider implementation
- Caching layer for repeated searches
- Rate limiting & retry logic
- Streaming search results
- Search history/context
- Custom provider plugins

## Success Criteria

1. ✅ `search` tool works with Brave API
2. ✅ Results are properly formatted for agents
3. ✅ Errors are returned to agent with clear messages
4. ✅ Can switch providers via config
5. ✅ Test coverage >80%
6. ✅ Passes linting (ruff)
7. ✅ Async implementation throughout

## Notes

- Keep implementation focused on Brave first
- Design for extensibility (SearXNG later)
- Prioritize agent UX in response formatting
- Document provider-specific configuration
