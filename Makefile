.PHONY: help install dev run test lint format type-check clean pre-commit

# Default target
help:
	@echo "Life Organizer Backend - Available Commands"
	@echo ""
	@echo "  make install      - Install production dependencies"
	@echo "  make dev          - Install all dependencies including dev tools"
	@echo "  make run          - Run the development server"
	@echo "  make test         - Run tests with coverage"
	@echo "  make lint         - Run linter (Ruff)"
	@echo "  make format       - Format code with Ruff"
	@echo "  make type-check   - Run type checker (MyPy)"
	@echo "  make pre-commit   - Run all pre-commit hooks"
	@echo "  make clean        - Remove generated files and caches"
	@echo ""

# Install production dependencies only
install:
	uv sync

# Install all dependencies including dev tools
dev:
	uv sync --all-extras
	uv run pre-commit install

# Run the development server
run:
	uv run uvicorn life_organizer.main:app --reload --host 0.0.0.0 --port 8000

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
