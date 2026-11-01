# life-organizer-be

The conventions for everyone who changes this repository, people and sail agents alike.

## The service

Life Organizer's backend is a personal FastAPI service with one user and one maintainer. It is a budget capture and
query API: it classifies free-text and screenshot input with Claude and stores budget transactions, budget plans and
feedback in PostgreSQL, for the iOS app. Every protected route sits behind the API key checked in
`src/life_organizer/auth.py`.

The meals and recipes endpoints were removed (LIFE-29); only the model `src/life_organizer/db/models/meals.py` remains.

Production runs on the maintainer's own machine behind Cloudflare at `https://org.ivot.dev`.

## Module map

One package, `src/life_organizer/`:

- `api/routes/`: a FastAPI `APIRouter` per domain (`budget.py`, `feedback.py`), included in `main.py`. Routes stay
  thin: they validate, call a service, and map its result or error to a response.
- `services/`: the business logic. `budget_service.py` for the budget domain; `claude_service.py` owns every call to the
  Anthropic API.
- `schemas/`: Pydantic v2 request and response models, and the shared enums in `schemas/enums.py`.
- `db/models/`: SQLAlchemy 2.0 declarative models on `db/base.py`'s `Base`. Sessions come from `db/session.py`'s
  `async_session_factory`, used as `async with async_session_factory() as session:`; every database call is awaited.
- `prompts/`: the Claude prompt files, read by `services/claude_service.py`.
- `config.py`: the settings (`pydantic-settings`, from the environment and `.env`). `auth.py`: the API-key dependency.
  `rate_limit.py`: the slowapi `limiter`.
- `config/` at the repository root: the JSON category and keyword maps.
- `alembic/versions/`: the migrations.
- `tests/`: mirrors the package (`tests/api/`, `tests/services/`, `tests/schemas/`, `tests/db/`).

## Commands

- `make dev`: install dependencies and the pre-commit hooks.
- `make run` / `make stop`: start and stop the dev server. They kill whatever holds port 8000, so they are for a person
  at the machine, never for a sail run.
- `scripts/gate.sh`: the one way to verify a change: `ruff check`, `ruff format --check`, `mypy src` and
  `pytest -m "not integration"`, with placeholder keys and no `.env`. `scripts/gate.sh --base <commit>` skips it when
  only docs or `.sail/` changed. It also runs `scripts/test-version.sh`.
- `scripts/version.sh`: prints the next semantic version from the Conventional Commits since the last `v*` tag;
  `--write` sets it in `pyproject.toml`, `uv.lock` and `openapi.yaml`, `--notes` prints the release notes. CI's
  `release` job uses it on `staging`.
- `make test-integration`: the tests that call the real Anthropic API; needs `ANTHROPIC_API_KEY` (or
  `CLAUDE_API_KEY`).
- Migrations: `make db-migrate` (or `PYTHONPATH=src uv run alembic upgrade head`) applies them, and
  `PYTHONPATH=src uv run alembic revision -m "describe the change"` creates one. `--autogenerate` needs a reachable
  database.

## Conventions

- Python 3.14, typed throughout: mypy runs `strict` over `src/`. Ruff lints and formats, line length 100.
- Async SQLAlchemy 2.0 with every call awaited, and Pydantic v2.
- Protected routes depend on `auth.py`. Routes that call Claude carry `@limiter.limit(...)` from `rate_limit.py`.
- Migrations are Alembic, written with both `upgrade()` and `downgrade()`. A model change ships with its migration in
  the same commit.
- `openapi.yaml` is the API's contract with the clients: a new or changed endpoint updates it.
- Tests are pytest, with `asyncio_mode = "auto"` (no decorator on async tests) and the markers `unit`, `integration`
  and `slow`. Unit tests reach no database and no network: the session factory and the Claude client are mocked with
  `unittest.mock`, and `tests/conftest.py` bypasses the API-key check. A test that calls the real Anthropic API is marked
  `@pytest.mark.integration` and stays out of the gate.

## Git

- Branch from `staging` and open pull requests into `staging`, never `main`. `main` is synced from `staging`.
- Commits are Conventional Commits, `<type>(<scope>): <what it does> (<ticket>)`, the scope the domain or module in
  kebab case (`budget`, `meals`, `feedback`, `auth`, `logging`, `gate`, `sail`).
- Stage paths by name, never `git add -A` or `git add .`.

## Linear

Team `LIFE`, shared with the iOS and web repositories. This repository's tickets carry the label `Backend`; `factory-be`
marks a ticket for the factory to build and `groom-be` one to groom.

## Never

- Never read or write `.env`, and never commit a credential: settings come from the environment.
- Never run a migration, `psql` or Docker from a sail run: the database and containers are the machine's.

## Doc map

Read a doc when its line matches your task.

`docs/features/`:

- `budget-plan-crud.md`: budget plans, PostgreSQL upserts, or changes to the `budget.plans` schema.
- `budget-screenshot-import.md`: Claude Vision, the screenshot parsing prompt, or new input modalities for import.
- `direct-budget-flow.md`: new LLM-powered budget services, the transaction pipeline, or Claude retry behavior.
- `meals-schema-and-models.md`: the remaining meals model and its migration (the endpoints it describes are gone).
- `misclassification-feedback-model.md`: the feedback schema, or endpoints for classification corrections.
- `rate-limiting-llm-endpoints.md`: rate limits on endpoints that call Claude, or 429 and `Retry-After` behavior.
- `transaction-query-pagination.md`: paginated list endpoints, optional filters, or query indexes.

`docs/development/`:

- `setup.md`: setting up a local environment.
- `docker.md`: Docker Compose, container logs, database access and troubleshooting.
- `ci.md`: the CI jobs and reproducing them locally.
- `deployment-guide.md`: environment variables and where production runs.

`docs/architecture/`:

- `architecture.md`, `backend-architecture-high-level-design.md`: the system's design.
- `api-contracts-life-organizer-be.md`: the endpoints' contracts.
- `data-models-life-organizer-be.md`: the database models.

`openapi.yaml`: the clients' contract; read it and update it when an endpoint changes.
