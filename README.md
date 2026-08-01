# YAMS

> Yet Another MCP Server

YAMS is a batteries-included MCP server that provides the common tools most coding agents need:

* Web search
* Fetching and parsing web pages
* File system access
* Shell command execution
* Git integration
* Basic utility tools

Built in Python. Run with `uv`.

No Electron.
No Docker required.
No enterprise platform.
Just tools.

---

## Why?

Every agent stack ends up rebuilding the same MCP tools:

* search
* fetch
* grep
* git
* run commands
* read/write files

YAMS packages the boring, standard functionality into a single MCP server that works well locally, in CI, or on remote hosts.

The goal is not to be clever.

The goal is to be useful.

---

## Features

* Fast startup
* Single-process architecture
* Async Python implementation
* Designed for local-first workflows
* Works well with Claude Code-style agents
* Easy to extend with custom tools
* Sensible defaults
* Minimal configuration

---

## Installation

### From GitHub

```bash
uv tool install git+https://github.com/carlosroman/yams.git
```

Or run without installing:

```bash
uvx --from git+https://github.com/carlosroman/yams.git yams
```

---

## Quick Start

Start the server:

```bash
uvx yams
```

Example MCP client configuration:

```json
{
  "mcpServers": {
    "yams": {
      "command": "uvx",
      "args": ["yams"]
    }
  }
}
```

---

## Included Tools

Planned tools (none implemented yet):

| Tool         | Description               | Status      |
| ------------ | ------------------------- | ----------- |
| `search`     | Search the web            | ⏳ Planned  |
| `fetch`      | Fetch and parse web pages | ⏳ Planned  |
| `shell`      | Execute shell commands    | ⏳ Planned  |
| `read_file`  | Read files                | ⏳ Planned  |
| `write_file` | Write files               | ⏳ Planned  |
| `grep`       | Search project contents   | ⏳ Planned  |
| `git_status` | Git status                | ⏳ Planned  |
| `git_diff`   | Git diff                  | ⏳ Planned  |
| `git_commit` | Create commits            | ⏳ Planned  |
| `list_dir`   | List directories          | ⏳ Planned  |

More tools will be added over time.

---

## Philosophy

YAMS follows a few simple rules:

### Local-first

Your tools should work on your machine without requiring cloud infrastructure.

### Unix-style

Small composable tools beat giant opaque systems.

### Predictable over magical

Agents need reliable tooling more than “AI-native” abstractions.

### Boring technology wins

Python.
JSON.
stdio.
HTTP.

These things work.

---

## Development

Clone the repository:

```bash
git clone https://github.com/your-org/yams.git
cd yams
```

Install dependencies:

```bash
uv sync
```

Run the server:

```bash
uv run yams
```

Run tests:

```bash
uv run pytest
```

Lint:

```bash
uv run ruff check
```

Format:

```bash
uv run ruff format
```

---

## Project Structure

```text
yams/
├── pyproject.toml
├── src/yams/
│   ├── server.py
│   ├── tools/
│   ├── transport/
│   └── config/
├── tests/
└── README.md
```

---

## Roadmap

* Browser automation tools
* Better sandboxing
* Remote execution support
* Tool permissions
* Persistent sessions
* Caching
* Authentication support
* Plugin system

---

## Non-Goals

YAMS is not:

* an agent framework
* an orchestration platform
* a workflow engine
* a hosted service
* an IDE replacement

It is just an MCP server.

---

## Name

Yes, the name is recursive.

No, this probably didn't need to exist.

---

## License

MIT
