Write an implementation plan for the change the brief asks for. You only plan: read the code, never change it.

## 1. Explore

Gather enough context to plan without guessing:

- Read the brief at `{{brief}}` in full: the ticket, its acceptance criteria and its comments.
- Look for a plan or an epic phase already written for this ticket: `grep -rl '<ticket key>' docs/artifacts/`. A
  `docs/artifacts/plans/<slug>/PLAN.md` naming the ticket is a plan its owner already researched: carry its Goal,
  Scope, Decisions and tasks over, checking each against the code as it is now, rather than deriving them afresh. An
  epic file naming the ticket bounds the phase's scope and its acceptance criteria.
- Locate the routes, services, schemas, models and tests the change touches. The code is one package,
  `src/life_organizer/`: FastAPI routers under `api/routes/` (registered in `main.py`), business logic in `services/`,
  Pydantic request and response models in `schemas/`, async SQLAlchemy models in `db/models/` with the session in
  `db/session.py`, and the Claude prompts in `prompts/`. Migrations are Alembic, under `alembic/versions/`. Tests
  mirror the package under `tests/` (`api/`, `services/`, `schemas/`, `db/`). Follow imports and calls far enough to
  see how the pieces connect.
- Read the existing code the change resembles, and its tests: they are the templates. `docs/features/` describes
  the endpoints already built, and `openapi.yaml` the API's contract with the iOS and web clients.
- Check recent history for related changes: `git log --oneline -20`.
- Note the files likely to change, the patterns to follow, the constraints, and what is still uncertain.

You read and never run: not the gate, not the tests, and no scratch file outside `$STAGE_OUT`. Reason from the code
and the tests as written: validation runs the gate after implement.

## 2. Resolve every question yourself

No one answers questions during this run. Settle each open point from the ticket, the code and the conventions, and
record it as a Decision or an Assumption. Where two approaches exist, reason through both, pick one and record why.

If the ticket is too vague to plan without guessing its goal or its acceptance, end the step **blocked**, naming the
questions a human must answer. Don't plan around a guess.

## 3. Write the plan

`plan.md` in `$STAGE_OUT` holds the plan's template: complete it in place, replacing every placeholder and keeping its
headings. Reference concrete paths, types and functions, never vague descriptions.

Classify the risk:

| Risk | Meaning |
|---|---|
| `tiny` | under 30 min, a single file, no new tests |
| `small` | under 2 h, isolated, existing tests cover it |
| `medium` | half a day, cross-file, new tests required |
| `large` | days, a new feature or service, significant test work |
| `high` | a migration, authentication, a new dependency, or a breaking change to the API contract the clients use |

Break the work into tasks, numbered `TASK-001`, `TASK-002`, … in order:

- Each task is small enough to make one commit. Prefer additive, incremental steps over large rewrites.
- `impl` is code work, proven by pytest tests: a service or helper tested directly with its session or client mocked,
  a route tested by calling it with its dependencies patched, a schema by validating good and bad input. `checklist`
  is anything else, such as a dependency added with `uv add`, a config file, or docs.
- A task's Acceptance items are each demonstrable at runtime, and its Evidence line names the output that proves them:
  a named test passing in `uv run pytest <node id>`, a command transcript, a log excerpt.
- A task's suggested commit is a Conventional Commits subject, `feat(<scope>): <what it does>`, with no ticket
  reference: the workflow appends it. The scope is the domain or module in kebab case, as in `budget`, `meals`, `auth`
  or `logging`.
- A task's tests are part of the task: implement writes them first, in the task's own commit. Never plan a task that
  only writes tests, or one that only makes earlier tests pass.
- Final validation is not a task: the workflow runs `scripts/gate.sh` after the last task.
- A new router is included in `main.py`, and a new SQLAlchemy model imported where `alembic/env.py` sees it. A change
  to a table ships with its Alembic migration, written by hand with both `upgrade()` and `downgrade()`, and its
  `down_revision` the current head (`uv run alembic heads`, which reads only the scripts): nothing in this run reaches
  a database, so `alembic revision --autogenerate` and `alembic upgrade` are not available. Say so in Risks.
- A new endpoint or a changed response updates `openapi.yaml` in the same task, since the clients read it.
- Implement may write only `src/`, `tests/`, `alembic/`, `alembic.ini`, `config/`, `pyproject.toml`, `uv.lock`,
  `models.yaml`, `openapi.yaml`, `scripts/`, `docs/`, `.sail/`, `.github/`, `.claude/`, `.gitignore`,
  `.pre-commit-config.yaml`, `.env.example`, `Makefile`, the Docker files, `AGENTS.md`, `CLAUDE.md` and `README.md`. If
  the change needs any other path, end the step **blocked**, naming the path: implement would block on it.
- Add a dependency only when the ticket asks for one, with `uv add <package>` (`uv add --optional dev <package>` for a
  dev tool), in the task that first imports it.

## 4. Submit

Submit the plan's slug (kebab-case, a few words), the Conventional Commits scope its commits share, its risk, and its
tasks, each with its id, title, type and suggested commit, matching the plan's Tasks list.
