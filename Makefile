.PHONY: setup check test lint
setup:
	uv sync
check:
	uv run python scripts/m0_check.py
test:
	uv run pytest -q
lint:
	uv run ruff check src tests
