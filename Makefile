.PHONY: install lint format test run clean

install:
	@(uv sync)

lint:
	@(uv run ruff check)

format:
	@(uv run ruff format .)

check: lint format

test:
	@(uv run pytest -v)

test-watch:
	@(uv run pytest -v --looponfail)

run:
	@(uv run yams)

clean:
	@(rm -rf .pytest_cache .ruff_cache __pycache__ src/__pycache__ src/yams/__pycache__)
	@(find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true)
