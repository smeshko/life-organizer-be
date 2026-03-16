.PHONY: help install dev run stop restart test test-unit test-integration test-fast lint format type-check clean pre-commit db-setup db-migrate docker-build docker-up docker-down docker-logs docker-shell docker-db

# Default target
help:
	@echo "Life Organizer Backend - Available Commands"
	@echo ""
	@echo "Development:"
	@echo "  make install      - Install production dependencies"
	@echo "  make dev          - Install all dependencies including dev tools"
	@echo "  make run          - Run the development server (auto-stops existing server)"
	@echo "  make stop         - Stop the development server"
	@echo "  make restart      - Restart the development server"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test              - Run all tests (unit + integration) with coverage"
	@echo "  make test-unit         - Run only unit tests (fast, no API calls)"
	@echo "  make test-integration  - Run only integration tests (requires API key)"
	@echo "  make test-fast         - Run unit tests only (alias for test-unit)"
	@echo "  make lint              - Run linter (Ruff)"
	@echo "  make format            - Format code with Ruff"
	@echo "  make type-check        - Run type checker (MyPy)"
	@echo "  make pre-commit        - Run all pre-commit hooks"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build - Build Docker images"
	@echo "  make docker-up    - Start all services (app + database)"
	@echo "  make docker-down  - Stop all services"
	@echo "  make docker-logs  - View service logs"
	@echo "  make docker-shell - Open shell in app container"
	@echo "  make docker-db    - Connect to PostgreSQL database"
	@echo ""
	@echo "Database:"
	@echo "  make db-setup     - Start DB container and run migrations"
	@echo "  make db-migrate   - Run pending migrations"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean        - Remove generated files and caches"
	@echo ""

# Install production dependencies only
install:
	uv sync

# Install all dependencies including dev tools
dev:
	uv sync --all-extras
	uv run pre-commit install

# Configuration
PORT ?= 8000

# Stop the development server
stop:
	@echo "Stopping development server on port $(PORT)..."
	@lsof -ti:$(PORT) | xargs kill -9 2>/dev/null || echo "No server running on port $(PORT)"

# Run the development server (auto-stops existing server)
run: stop
	@echo "Starting development server on port $(PORT)..."
	PYTHONPATH=src uv run python -m uvicorn life_organizer.main:app --reload --host 0.0.0.0 --port $(PORT)

# Restart the development server
restart: stop run

# Run all tests (unit + integration) with coverage
test:
	@echo "Running all tests (unit + integration)..."
	@echo "Note: Integration tests require ANTHROPIC_API_KEY environment variable"
	uv run pytest

# Run only unit tests (fast, no API calls)
test-unit:
	@echo "Running unit tests only (no integration tests)..."
	uv run pytest -m "not integration" -v

# Run only integration tests (requires API key)
test-integration:
	@echo "Running integration tests (requires ANTHROPIC_API_KEY)..."
	@if [ -z "$$ANTHROPIC_API_KEY" ] && [ -z "$$CLAUDE_API_KEY" ]; then \
		echo ""; \
		echo "ERROR: API key not found!"; \
		echo "Please set ANTHROPIC_API_KEY or CLAUDE_API_KEY environment variable:"; \
		echo "  export ANTHROPIC_API_KEY=your_key_here"; \
		echo ""; \
		exit 1; \
	fi
	uv run pytest -m integration -v

# Alias for test-unit (commonly used for CI/CD)
test-fast: test-unit

# Run linter
lint:
	uv run ruff check .

# Format code
format:
	uv run ruff format .
	uv run ruff check --fix .

# Run type checker
type-check:
	uv run mypy src

# Run all pre-commit hooks manually
pre-commit:
	uv run pre-commit run --all-files

# Clean generated files
clean:
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Database commands
db-migrate:
	@echo "Running database migrations..."
	PYTHONPATH=src uv run alembic upgrade head

db-setup:
	@echo "Starting database container..."
	docker compose up -d db
	@echo "Waiting for database to be ready..."
	@until docker compose exec db pg_isready -U life_organizer > /dev/null 2>&1; do sleep 1; done
	@echo "Database is ready. Running migrations..."
	PYTHONPATH=src uv run alembic upgrade head
	@echo "Database setup complete."

# Docker commands
docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting all services (app + database)..."
	@echo "App will be available at http://localhost:8000"
	@echo "API docs at http://localhost:8000/api/v1/docs"
	docker-compose up

docker-down:
	@echo "Stopping all services..."
	docker-compose down

docker-logs:
	@echo "Viewing service logs (Ctrl+C to exit)..."
	docker-compose logs -f

docker-shell:
	@echo "Opening shell in app container..."
	docker-compose exec app bash

docker-db:
	@echo "Connecting to PostgreSQL database..."
	docker-compose exec db psql -U life_organizer -d life_organizer
