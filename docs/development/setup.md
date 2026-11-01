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

## Environment Variables

Settings are read from the environment and `.env` (see `src/life_organizer/config.py` and `.env.example`).

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_KEY` | Yes | - | Key clients send to authenticate requests |
| `CLAUDE_API_KEY` | Yes | - | Anthropic Claude API key |
| `DEBUG` | No | `false` | Enable debug mode |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `HOST` | No | `0.0.0.0` | Server host |
| `PORT` | No | `8000` | Server port |
| `DATABASE_URL` | No | local PostgreSQL | PostgreSQL connection URL |
| `CORS_ORIGINS` | No | see `config.py` | Allowed CORS origins |

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
make clean       # Remove generated files and caches
```

### Available Commands

| Command | Description |
|---------|-------------|
| `make dev` | Install all dependencies and dev tools |
| `make run` / `make stop` / `make restart` | Start, stop or restart the dev server (`run` stops an existing one first) |
| `make test` | Run all tests with coverage |
| `make test-unit` | Unit tests only (no API calls) |
| `make test-integration` | Integration tests (requires an API key) |
| `make docker-build` / `docker-up` / `docker-down` | Build, start and stop the Docker services (see [DOCKER.md](../../DOCKER.md)) |
| `make docker-logs` / `docker-shell` / `docker-db` | Logs, an app shell and a PostgreSQL shell |

### Git Branching

- `main` - production-ready code
- `staging` - development integration; pull requests go here
- Feature branches: `feature/`, `refactoring/`, `documentation/`, `hotfix/`

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

### Commit Message Format

Use conventional commits:
- `feat(scope): description` - new feature
- `fix(scope): description` - bug fix
- `docs(scope): description` - documentation
- `refactor(scope): description` - refactoring
- `test(scope): description` - tests
- `chore(scope): description` - maintenance

## Pre-commit Hooks

Hooks run automatically on `git commit`:

- Trailing whitespace removal
- YAML/JSON/TOML syntax check
- Large file detection (max 1MB)
- Merge conflict detection
- Private key detection
- Ruff linting and formatting
- MyPy type checking
- OpenAPI spec validation

## Database Migrations

```bash
# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Check current version
alembic current

# Rollback one migration
alembic downgrade -1
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
