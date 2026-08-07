# Plan: Add `webfetch` Tool to YAMS MCP Server

## Summary

Add a `webfetch` tool that fetches URLs using Scrapling AsyncFetcher and converts content to markdown using Trafilatura (HTML/XML/JSON) or MarkItDown (PDF). The implementation follows the existing search tool patterns and includes comprehensive tests with a local test server.

---

## Architecture

```
src/yams/
├── server.py                    # Add webfetch tool registration
├── tools/
│   ├── __init__.py              # Export create_fetch_tool
│   └── fetch/
│       ├── __init__.py          # Module exports
│       ├── settings.py          # FetchSettings
│       ├── tool.py              # create_fetch_tool()
│       └── providers/
│           ├── __init__.py
│           ├── base.py          # Fetcher ABC, FetchResponse
│           ├── scrapling_fetcher.py  # AsyncFetcher implementation
│           └── converters/
│               ├── __init__.py
│               ├── base.py      # ContentConverter ABC
│               ├── trafilatura.py    # HTML/XML/JSON → markdown
│               └── markitdown.py     # PDF → markdown

tests/
├── fixtures/
│   └── test_page.html           # Simple HTML test page
├── unit/
│   ├── test_fetch_tool.py       # Tool validation tests
│   ├── test_fetch_providers.py  # Provider & converter tests
│   └── test_fetch_settings.py   # Settings tests
└── integration/
    └── test_fetch_real.py       # Real HTTP tests with local server
```

---

## Dependencies (pyproject.toml)

```toml
dependencies = [
    "mcp>=2.0.0",
    "httpx>=0.28.0",
    "pydantic>=2.13.0",
    "pydantic-settings>=2.14.0",
    "python-dotenv>=1.2.0",
    # New:
    "scrapling>=0.4.0",
    "trafilatura>=2.0.0",
    "markitdown>=0.1.0",
]

[dependency-groups]
test = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-httpx>=0.30.0",  # For mocking HTTP requests in tests
]
```

---

## Component Specifications

### 1. FetchSettings (`src/yams/tools/fetch/settings.py`)

```python
class FetchSettings(BaseSettings):
    provider: Literal["scrapling"] = "scrapling"
    timeout: int = 30
    max_size: int = 1048576  # 1MB
    follow_redirects: bool = True
    user_agent: str | None = None
    scrapling_stealthy: bool = False
    scrapling_headless: bool = False
    
    model_config = {
        "env_prefix": "YAMS_FETCH_",
        "extra": "ignore",
    }
```

**Environment Variables:**
- `YAMS_FETCH_PROVIDER`, `YAMS_FETCH_TIMEOUT`, `YAMS_FETCH_MAX_SIZE`
- `YAMS_FETCH_FOLLOW_REDIRECTS`, `YAMS_FETCH_USER_AGENT`
- `YAMS_FETCH_SCRAPLING_STEALTHY`, `YAMS_FETCH_SCRAPLING_HEADLESS`

---

### 2. Base Classes (`src/yams/tools/fetch/providers/base.py`)

```python
@dataclass
class FetchResponse:
    url: str
    content: str
    content_type: str
    status_code: int
    title: str | None = None
    extracted_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict = field(default_factory=dict)

class ContentConverter(ABC):
    @abstractmethod
    def convert(self, content: bytes | str, content_type: str) -> str: ...

class Fetcher(ABC):
    @abstractmethod
    async def fetch(self, url: str) -> FetchResponse: ...
```

---

### 3. Scrapling Fetcher (`src/yams/tools/fetch/providers/scrapling_fetcher.py`)

**Key Features:**
- Uses `scrapling.fetchers.AsyncFetcher`
- Validates URL format using `urllib.parse`
- Checks `content-length` header against `max_size`
- Handles redirects based on `follow_redirects`
- Routes to appropriate converter based on `content-type`

**Error Handling:**
- Invalid URL → `ValueError`
- Fetch timeout → `RuntimeError`
- Size exceeded → `RuntimeError`
- HTTP error → `RuntimeError` with status code

---

### 4. Converters

#### TrafilaturaConverter (`src/yams/tools/fetch/providers/converters/trafilatura.py`)

- **HTML**: `trafilatura.extract(html, output_format="markdown")`
- **JSON**: `json.dumps(json.loads(content), indent=2)` wrapped in ```json code block
- **XML**: `xml.dom.minidom` pretty-print wrapped in ```xml code block

#### MarkItDownConverter (`src/yams/tools/fetch/providers/converters/markitdown.py`)

- **PDF**: `MarkItDown().convert_stream(BytesIO(content))`

---

### 5. Tool Wrapper (`src/yams/tools/fetch/tool.py`)

```python
def create_fetch_tool(settings: FetchSettings):
    provider = create_fetch_provider(settings)
    
    async def webfetch(
        url: str,
        format: Literal["markdown", "text", "html"] = "markdown",
    ) -> dict:
        """
        Fetch a URL and return its content.
        
        Args:
            url: The URL to fetch
            format: Output format (default: "markdown")
        
        Returns:
            dict with url, content, content_type, status_code, title, extracted_at
        
        Raises:
            ValueError: If URL is invalid or empty
            RuntimeError: If fetch fails
        """
        # Validate URL not empty
        # Validate URL format (http/https)
        # Call provider.fetch(url)
        # Convert content if format != "markdown"
        # Return dict with url, content, content_type, status_code, title, extracted_at
        
    return webfetch
```

---

### 6. Server Registration (`src/yams/server.py`)

```python
def init_server(
    search_settings: SearchSettings | None = None,
    fetch_settings: FetchSettings | None = None,
) -> MCPServer:
    server = MCPServer("yams")
    
    # ... existing search tool ...
    
    # New fetch tool
    fetch_fn = create_fetch_tool(fetch_settings or FetchSettings())
    current_year = datetime.now(tz=UTC).year
    server.tool(
        name="webfetch",
        title="Fetch Web Page",
        annotations=ToolAnnotations(
            read_only_hint=True,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=False,
        ),
        description=(
            f"Fetch and parse a web page, returning content in markdown format. "
            f"Use this to read the full content of web pages found via search or provided by the user. "
            f"Supports HTML, JSON, XML, and PDF content types. "
            f"Trafilatura extracts main content from HTML pages, "
            f"MarkItDown handles PDF conversion. "
            f"The current year is {current_year}."
        )
    )(fetch_fn)
    
    return server
```

---

## Test Infrastructure

### Test Fixtures (`tests/fixtures/test_page.html`)

```html
<!DOCTYPE html>
<html>
<head><title>Test Page</title></head>
<body>
    <nav>Navigation (should be stripped)</nav>
    <main>
        <h1>Main Heading</h1>
        <p>This is the main content for testing.</p>
        <article>
            <h2>Article Title</h2>
            <p>Article content goes here.</p>
        </article>
    </main>
    <footer>Footer (should be stripped)</footer>
</body>
</html>
```

### Local Test Server

Use `pytest-httpx` or `httpx`'s `MockTransport` to serve test fixtures without external dependencies.

---

## Test Files

### Unit Tests

1. **`tests/unit/test_fetch_settings.py`** (15 tests)
   - Default values
   - Environment variable loading
   - Validation errors

2. **`tests/unit/test_fetch_tool.py`** (12 tests)
   - URL validation (empty, invalid format)
   - Format parameter handling
   - Mocked provider success/error
   - Response format validation

3. **`tests/unit/test_fetch_providers.py`** (25 tests)
   - ScraplingFetcher initialization
   - URL validation
   - Size limit checking
   - Converter routing
   - TrafilaturaConverter (HTML, JSON, XML)
   - MarkItDownConverter (PDF)
   - Error handling (404, timeout, rate limit)

### Integration Tests

**`tests/integration/test_fetch_real.py`** (8 tests)
- Real fetch from local test server
- HTML extraction with trafilatura
- JSON/XML pretty-printing
- PDF conversion (if test PDF available)
- 404 error handling
- Timeout handling
- Redirect handling

---

## Implementation Phases

### Phase 1: Core Infrastructure (30 min)
- [ ] Create directory structure
- [ ] Implement `FetchSettings`
- [ ] Create base classes (ABCs, dataclasses)
- [ ] Write unit tests for settings

### Phase 2: Converters (45 min)
- [ ] Implement `TrafilaturaConverter`
- [ ] Implement `MarkItDownConverter`
- [ ] Write unit tests for converters
- [ ] Create test fixtures (HTML, JSON, XML, PDF)

### Phase 3: Fetcher (45 min)
- [ ] Implement `ScraplingFetcher`
- [ ] Add URL validation
- [ ] Add size limit checking
- [ ] Write unit tests for fetcher

### Phase 4: Tool Wrapper (30 min)
- [ ] Implement `create_fetch_tool()`
- [ ] Add parameter validation
- [ ] Write unit tests for tool
- [ ] Update `tools/__init__.py`

### Phase 5: Server Integration (15 min)
- [ ] Update `server.py` to register webfetch
- [ ] Test server startup
- [ ] Update `README.md`

### Phase 6: Integration Tests (45 min)
- [ ] Create test fixtures
- [ ] Set up local test server
- [ ] Write integration tests
- [ ] Run all tests

**Total Estimated Time:** ~3 hours

---

## Files to Create (17 files)

```
src/yams/tools/fetch/__init__.py
src/yams/tools/fetch/settings.py
src/yams/tools/fetch/tool.py
src/yams/tools/fetch/providers/__init__.py
src/yams/tools/fetch/providers/base.py
src/yams/tools/fetch/providers/scrapling_fetcher.py
src/yams/tools/fetch/providers/converters/__init__.py
src/yams/tools/fetch/providers/converters/base.py
src/yams/tools/fetch/providers/converters/trafilatura.py
src/yams/tools/fetch/providers/converters/markitdown.py
tests/fixtures/test_page.html
tests/fixtures/test_data.json
tests/fixtures/test_data.xml
tests/unit/test_fetch_settings.py
tests/unit/test_fetch_tool.py
tests/unit/test_fetch_providers.py
tests/integration/test_fetch_real.py
```

## Files to Modify (4 files)

```
pyproject.toml                    # Add dependencies
src/yams/server.py                # Register webfetch tool
src/yams/tools/__init__.py        # Export create_fetch_tool
README.md                         # Update tools table
```

---

## Future Extensibility

When adding Playwright support in v2:

1. Create `src/yams/tools/fetch/providers/playwright_fetcher.py`
2. Add `playwright` to `FetchSettings.provider` literal
3. Update `get_fetch_provider()` factory (similar to search providers)
4. No changes to converters or tool wrapper needed

---

## Design Decisions

### Why Scrapling AsyncFetcher?
- Async support matches YAMS server architecture
- Built-in stealth features for future anti-bot needs
- Good performance and reliability

### Why Trafilatura for HTML?
- Industry-standard for text extraction
- Handles main content extraction (strips nav/ads)
- Better than simple HTML-to-markdown conversion

### Why MarkItDown for PDF?
- Microsoft's library with good PDF support
- Can handle other document formats if needed later
- Returns clean markdown output

### Why Local Test Server?
- No external dependencies (httpbin is unreliable)
- Faster tests
- Full control over test scenarios
- Can test edge cases easily

### Why Raise Errors?
- Consistent with search tool behavior
- Clearer error propagation in MCP protocol
- Easier to debug

---

## Success Criteria

- [ ] Tool successfully fetches HTML pages and extracts main content
- [ ] JSON/XML responses are pretty-printed with code blocks
- [ ] PDFs are converted to markdown
- [ ] All unit tests pass (>90% coverage)
- [ ] All integration tests pass
- [ ] Lint and format checks pass
- [ ] Server starts without errors
- [ ] README updated with implementation status
