.PHONY: all install dev test docs servedocs docs-serve lint format build clean help

DOCS_ADDR ?= localhost:8123

all: install

help:
	@echo "ptm-pipeline development targets:"
	@echo "  make install  - install dependencies with uv"
	@echo "  make dev      - run CLI in development mode"
	@echo "  make test     - run tests"
	@echo "  make docs     - build the documentation site into public/"
	@echo "  make servedocs - serve the documentation with live reload (DOCS_ADDR=$(DOCS_ADDR));"
	@echo "                   make docs-serve is the same"
	@echo "  make lint     - run ruff linter"
	@echo "  make format   - format code with ruff"
	@echo "  make build    - build package"
	@echo "  make clean    - remove build artifacts"

install:
	uv sync

dev:
	uv run ptm-pipeline --help

test:
	uv run pytest tests/ -v

docs:
	uv run --group docs zensical build --clean --strict

servedocs docs-serve:
	uv run --group docs zensical serve --dev-addr $(DOCS_ADDR)

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
