# life-organizer-be conventions

The rules every sail agent in this repository follows. They stand in for the root `AGENTS.md` until it exists; then
`project.yaml`'s `conventions` points there and this file goes.

## The service

Life Organizer's backend is a personal FastAPI service with one user and one maintainer. It classifies free-text and
screenshot input with Claude and stores budget transactions, budget plans, meals and feedback in PostgreSQL, for the
iOS and web clients. It is not distributed beyond that one person.

## Code

- Python 3.14, typed throughout: mypy runs `strict` over `src/`. Ruff lints and formats, line length 100.
- One package, `src/life_organizer/`:
  - `api/routes/<domain>.py`: a FastAPI `APIRouter` per domain (`budget`, `meals`, `feedback`), included in `main.py`.
    Routes stay thin: they validate, call a service, and map its result or error to a response.
  - `services/<domain>_service.py`: the business logic. `claude_service.py` owns every call to the Anthropic API.
  - `schemas/`: Pydantic v2 request and response models, and the shared enums in `schemas/enums.py`.
  - `db/models/<domain>.py`: SQLAlchemy 2.0 declarative models on `db/base.py`'s `Base`. Sessions come from
    `db/session.py`'s `async_session_factory`, used as `async with async_session_factory() as session:`; every
    database call is `await`ed.
  - `prompts/`: the Claude prompts, as files. `config.py` holds the settings (`pydantic-settings`, read from the
    environment and `.env`); `auth.py` the API-key dependency every protected route uses.
- Migrations are Alembic, under `alembic/versions/`, written with both `upgrade()` and `downgrade()`. A model change
  ships with its migration in the same commit.
- `openapi.yaml` is the API's contract with the clients: a new or changed endpoint updates it.

## Testing

- pytest, under `tests/`, mirroring the package (`tests/api/`, `tests/services/`, `tests/schemas/`, `tests/db/`).
  Async tests need no decorator: `asyncio_mode = "auto"`.
- Unit tests reach no database and no network: the session factory and the Claude client are mocked with
  `unittest.mock`. `tests/conftest.py` bypasses the API-key check for every test.
- A test that calls the real Anthropic API is marked `@pytest.mark.integration`; it needs `ANTHROPIC_API_KEY` and stays
  out of the gate.

## Verifying

- `scripts/gate.sh` is the one way to verify a change: `ruff check`, `ruff format --check`, `mypy src` and
  `pytest -m "not integration"`. It exits non-zero on any failure, and runs with placeholder keys, so it needs no
  `.env`. `--base <commit>` skips it when only docs or `.sail/` changed.
- `make` targets are for a person at the machine: `make run` and `make stop` kill whatever holds port 8000.

## Git

- Pull requests go into `staging`, never `main`.
- Commits are Conventional Commits, `<type>(<scope>): <what it does> (<ticket>)`, the scope the domain or module in
  kebab case (`budget`, `meals`, `feedback`, `auth`, `logging`, `gate`, `sail`). Stage paths by name, never
  `git add -A` or `git add .`.

## Never

- Never read or write `.env`, and never commit a credential: settings come from the environment.
- Never run a migration, `psql` or Docker from a run: the database and containers are the machine's.
