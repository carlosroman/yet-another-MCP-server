# AGENTS.md

## Project Overview

YAMS (Yet Another MCP Server) - a Python MCP server providing common coding agent tools.

**Current state:** Early stage. README describes the vision; implementation is minimal.

## Toolchain

- **Package manager:** `uv`
- **Formatter/Linter:** `ruff`
- **Testing:** `pytest` (dependencies not yet installed)

## Developer Commands

```bash
# Install dependencies
uv sync

# Run the server
uv run yams

# Lint
uv run ruff check

# Format
uv run ruff format

# Tests
uv run pytest
```

## Architecture (Planned)

```
src/yams/
├── server.py      # MCP server entrypoint
├── tools/         # Built-in tools (search, fetch, shell, git, etc.)
├── transport/     # MCP transport layer
└── config/        # Configuration handling
```

## Planned Tools

- `search` - Web search
- `fetch` - Fetch and parse web pages
- `shell` - Execute shell commands
- `read_file` / `write_file` - File operations
- `grep` - Search project contents
- `git_status` / `git_diff` / `git_commit` - Git integration
- `list_dir` - List directories

## Key Conventions

- **Local-first:** Tools should work without cloud infrastructure
- **Unix-style:** Small, composable tools
- **Predictable over magical:** Reliable tooling over AI abstractions
- **Boring technology:** Python, JSON, stdio, HTTP

## Skills

### git-commit

This repo includes a `git-commit` skill for creating conventional commits.

To use it:
1. Stage your changes: `git add <files>`
2. Run: `git commit` (the skill will auto-detect type/scope and commit)

## Non-Goals

Not an agent framework, orchestration platform, workflow engine, hosted service, or IDE replacement. Just an MCP server.
