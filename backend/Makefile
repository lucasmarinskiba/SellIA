# SellIA Backend — Developer Convenience Commands
.PHONY: help test test-cov test-watch logs migrate lint format fix-deprecations shell

help: ## Show this help message
	@echo "SellIA Backend — Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

test: ## Run the full test suite
	docker exec ia_vendedor_backend pytest tests/ -v --tb=short

test-cov: ## Run tests with coverage report
	docker exec ia_vendedor_backend pytest tests/ --cov=app --cov-report=term-missing --tb=short

test-watch: ## Run tests in watch mode (requires pytest-watch)
	docker exec ia_vendedor_backend ptw tests/ -- -v --tb=short

test-file: ## Run a specific test file (usage: make test-file FILE=tests/test_foo.py)
	docker exec ia_vendedor_backend pytest $(FILE) -v --tb=short

logs: ## Tail backend container logs
	docker logs -f ia_vendedor_backend

migrate: ## Run Alembic migrations inside the backend container
	docker exec ia_vendedor_backend alembic upgrade head

migrate-create: ## Create a new Alembic revision (usage: make migrate-create MSG="add users table")
	docker exec ia_vendedor_backend alembic revision --autogenerate -m "$(MSG)"

lint: ## Run ruff linter
	docker exec ia_vendedor_backend ruff check app/ tests/

format: ## Run ruff formatter
	docker exec ia_vendedor_backend ruff format app/ tests/

fix-deprecations: ## Auto-fix utcnow() and class Config deprecations
	docker exec ia_vendedor_backend python scripts/fix_deprecations.py

shell: ## Open a bash shell inside the backend container
	docker exec -it ia_vendedor_backend bash
