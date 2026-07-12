# Ecommerce AI Design Director — developer commands.
# Run `make help` for the list. Targets are thin wrappers so the daily workflow
# is memorable and consistent across the team.

.DEFAULT_GOAL := help
SHELL := /bin/bash

# --------------------------------------------------------------------------- #
# Infrastructure
# --------------------------------------------------------------------------- #
.PHONY: up
up: ## Start Postgres, Redis, Qdrant (waits for health)
	docker compose up -d --wait

.PHONY: down
down: ## Stop and remove infrastructure containers
	docker compose down

.PHONY: logs
logs: ## Tail infrastructure logs
	docker compose logs -f

# --------------------------------------------------------------------------- #
# Python workspace
# --------------------------------------------------------------------------- #
.PHONY: install
install: ## Sync the uv workspace (all packages + dev tools)
	uv sync

.PHONY: api
api: ## Run the FastAPI app with autoreload
	uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: initdb
initdb: ## Create database tables from the ORM metadata (local dev)
	uv run python -c "import asyncio; from api.db.session import init_models; asyncio.run(init_models())"

# --------------------------------------------------------------------------- #
# Quality gates
# --------------------------------------------------------------------------- #
.PHONY: lint
lint: ## Ruff lint
	uv run ruff check .

.PHONY: format
format: ## Ruff format
	uv run ruff format .

.PHONY: typecheck
typecheck: ## mypy (strict)
	uv run mypy packages apps

.PHONY: test
test: ## Run the test suite
	uv run pytest

.PHONY: check
check: lint typecheck test ## Run all quality gates

# --------------------------------------------------------------------------- #
# Frontend
# --------------------------------------------------------------------------- #
.PHONY: web
web: ## Run the React console (Vite dev server)
	cd apps/web && npm run dev

.PHONY: web-install
web-install: ## Install web dependencies
	cd apps/web && npm install

# --------------------------------------------------------------------------- #
.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'
