.PHONY: help format lint lint-docs test typecheck typecheck-mypy typecheck-pyright check clean install deps-upgrade deps-upgrade-runtime deps-upgrade-dev

# Default target - show help
help:
	@echo "Available targets:"
	@echo ""
	@echo "  make format          - Format code with ruff"
	@echo "  make lint            - Lint code with ruff (no fixes)"
	@echo "  make lint-fix        - Lint code with ruff (auto-fix)"
	@echo "  make lint-docs       - Lint markdown documentation"
	@echo "  make test            - Run tests with coverage"
	@echo "  make test-fast       - Run tests without coverage"
	@echo "  make typecheck       - Run all type checkers (mypy + pyright)"
	@echo "  make typecheck-mypy  - Type check with mypy only"
	@echo "  make typecheck-pyright - Type check with pyright only"
	@echo "  make check           - Run all checks (format, lint, lint-docs, typecheck, test)"
	@echo "  make clean           - Remove generated files and caches"
	@echo "  make install         - Install dependencies with uv"
	@echo "  make deps-upgrade    - Upgrade runtime+dev dependency bounds, relock, sync, and run checks"
	@echo ""
	@echo "Common workflows:"
	@echo "  make format lint-fix - Format and auto-fix linting issues"
	@echo "  make check           - Run full CI-like verification"

# Code formatting
format:
	@echo "Formatting code with ruff..."
	uv run ruff format

# Code linting
lint:
	@echo "Linting code with ruff (check only)..."
	uv run ruff check

lint-fix:
	@echo "Linting code with ruff (auto-fix)..."
	uv run ruff check --fix

# Documentation linting
lint-docs:
	@echo "Linting markdown documentation..."
	npx markdownlint-cli2 "**/*.md"

# Testing
test:
	@echo "Running tests with coverage..."
	uv run pytest --cov=worksection_mcp --cov-report=html --cov-report=term

test-fast:
	@echo "Running tests without coverage..."
	uv run pytest

# Type checking
typecheck-mypy:
	@echo "Type checking with mypy..."
	uv run mypy . --check-untyped-defs

typecheck-pyright:
	@echo "Type checking with pyright..."
	uv run pyright

typecheck: typecheck-mypy typecheck-pyright
	@echo "All type checks passed!"

# Run all checks (CI-like)
check: format lint lint-docs typecheck test
	@echo ""
	@echo "✅ All checks passed!"

# Cleanup
clean:
	@echo "Cleaning up generated files..."
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete!"

# Install dependencies
install:
	@echo "Installing dependencies with uv..."
	uv sync --frozen --extra dev

# Dependency upgrade workflow
deps-upgrade-runtime:
	@echo "Upgrading runtime dependency bounds..."
	uv add --upgrade --bounds lower --no-sync \
		httpx pydantic pydantic-settings cryptography aiosqlite pillow \
		python-dotenv python-docx openpyxl python-pptx pypdf

deps-upgrade-dev:
	@echo "Upgrading dev dependency bounds..."
	uv add --optional dev --upgrade --bounds lower --no-sync \
		pytest pytest-asyncio pytest-cov respx ruff mypy pyright

deps-upgrade: deps-upgrade-runtime deps-upgrade-dev
	@echo "Relocking and syncing dependencies..."
	uv lock --upgrade
	uv sync --frozen --extra dev
	$(MAKE) check
