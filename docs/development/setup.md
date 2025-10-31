# Development Setup Guide

## Prerequisites

- Python 3.13 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Git

## Initial Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd life-organizer-be
   ```

2. **Install dependencies**:
   ```bash
   make dev
   ```

   This will:
   - Create a virtual environment with Python 3.13
   - Install all dependencies (production + development)
   - Install pre-commit hooks

3. **Configure environment**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your local settings.

4. **Verify setup**:
   ```bash
   make test        # Run tests
   make lint        # Check linting
   make type-check  # Check types
   ```

## Development Workflow

### Running the Server

```bash
make run
```

The server will start at http://localhost:8000 with auto-reload enabled.

### Running Tests

```bash
make test        # Run all tests with coverage
pytest tests/    # Run specific test directory
pytest -v        # Verbose output
```

### Code Quality

```bash
make format      # Auto-format code
make lint        # Check for issues
make type-check  # Type checking
make pre-commit  # Run all pre-commit hooks
```

### Making Changes

1. Create a feature branch from `staging`:
   ```bash
   git checkout staging
   git pull
   git checkout -b feature/your-feature
   ```

2. Make your changes

3. Run quality checks:
   ```bash
   make format
   make test
   ```

4. Commit (pre-commit hooks run automatically):
   ```bash
   git add .
   git commit -m "feat(scope): description"
   ```

5. Push and create PR to `staging`:
   ```bash
   git push origin feature/your-feature
   ```

## IDE Setup

### VSCode

Recommended extensions:
- Python (Microsoft)
- Ruff (Astral Software)
- Even Better TOML

Settings are provided in `.vscode/settings.json`.

### PyCharm

Configure the project to use the `.venv` virtual environment created by uv.

## Troubleshooting

### Virtual Environment Issues

If you encounter virtual environment issues:
```bash
rm -rf .venv
uv sync --all-extras
```

### Pre-commit Hook Failures

To update pre-commit hooks:
```bash
uv run pre-commit autoupdate
uv run pre-commit install
```

### Port Already in Use

If port 8000 is already in use:
```bash
PORT=8001 make run
```

Or edit `.env` and change the `PORT` value.
