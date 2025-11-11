.PHONY: help install dev run stop restart test lint format type-check clean pre-commit docker-build docker-up docker-down docker-logs docker-shell docker-db

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
	@echo "  make test         - Run tests with coverage"
	@echo "  make lint         - Run linter (Ruff)"
	@echo "  make format       - Format code with Ruff"
	@echo "  make type-check   - Run type checker (MyPy)"
	@echo "  make pre-commit   - Run all pre-commit hooks"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build - Build Docker images"
	@echo "  make docker-up    - Start all services (app + database)"
	@echo "  make docker-down  - Stop all services"
	@echo "  make docker-logs  - View service logs"
	@echo "  make docker-shell - Open shell in app container"
	@echo "  make docker-db    - Connect to PostgreSQL database"
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

# Stop the development server
stop:
	@echo "Stopping development server on port 8000..."
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "No server running on port 8000"

# Run the development server (auto-stops existing server)
run: stop
	@echo "Starting development server..."
	PYTHONPATH=src uv run python -m uvicorn life_organizer.main:app --reload --host 0.0.0.0 --port 8000

# Restart the development server
restart: stop run

# Run tests with coverage
test:
	uv run pytest

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
