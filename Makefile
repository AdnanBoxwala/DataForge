# Developer shortcuts. CI calls the same targets, so the command list lives
# here once rather than being duplicated across GitHub Actions and Jenkins.

.DEFAULT_GOAL := help
.PHONY: help install lint format format-check typecheck test test-unit test-integration test-regression check docs docs-strict docs-serve clean

help: ## Show this help
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Sync the virtual environment from uv.lock
	uv sync

lint: ## Lint with ruff
	uv run ruff check src tests examples docs

format: ## Reformat with ruff
	uv run ruff format src tests examples docs

format-check: ## Fail if anything is unformatted (CI)
	uv run ruff format --check src tests examples docs

typecheck: ## Type-check with mypy
	uv run mypy src/dataforge

test: ## Run the whole test suite
	uv run pytest

test-unit: ## Unit tests only (fast, no subprocesses)
	uv run pytest -m "not integration and not regression"

test-integration: ## End-to-end tests against the installed console script
	uv run pytest -m integration

test-regression: ## Compare pipeline output against the committed baseline
	uv run pytest -m regression

docs: ## Build the HTML documentation into docs/_build/html
	uv run sphinx-build -b html docs docs/_build/html

docs-strict: ## Build the docs, failing on any warning (CI)
	uv run sphinx-build -b html -W --keep-going docs docs/_build/html

docs-serve: ## Build the docs and serve them at http://localhost:8000
	uv run sphinx-build -b html docs docs/_build/html
	uv run python -m http.server 8000 --directory docs/_build/html

check: lint format-check typecheck test ## Everything CI runs

clean: ## Remove caches and generated reports
	rm -rf .pytest_cache .ruff_cache .mypy_cache output docs/_build
	find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} +
