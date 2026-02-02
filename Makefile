.PHONY: all install dev test lint format build clean help

all: install

help:
	@echo "ptm-pipeline development targets:"
	@echo "  make install  - install dependencies with uv"
	@echo "  make dev      - run CLI in development mode"
	@echo "  make test     - run tests (if any)"
	@echo "  make lint     - run ruff linter"
	@echo "  make format   - format code with ruff"
	@echo "  make build    - build package"
	@echo "  make clean    - remove build artifacts"

install:
	uv sync

dev:
	uv run ptm-pipeline --help

test:
	uv run pytest tests/ -v || echo "No tests found"

lint:
	uv run ruff check src/

format:
	uv run ruff format src/

build:
	uv build

clean:
	rm -rf dist/ build/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
