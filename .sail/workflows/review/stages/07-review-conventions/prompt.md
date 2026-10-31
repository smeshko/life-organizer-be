Review this pull request for one question: does the change follow this repository's conventions? Five other reviewers cover requirements, architecture, bugs, tests and security at the same time, and
validation runs `scripts/gate.sh` beside you: ruff check, ruff format, mypy strict and the unit tests. Stay on
your question.

The change is `git diff {{base}}...HEAD`, its commits are `git log {{base}}..HEAD`, the pull request is described at
`{{brief}}`, and what it should do at `{{requirements}}`. Read past the diff: the code around each change, its callers
and its tests are where most problems hide.

You review only. Don't change any file, and don't run the gate or the tests: validation runs them beside you, and
the tests need no second run. Read the code instead, with `git grep`, the Read tool and `sed -n`.

## Method

1. Read the conventions appended below first: they are the rules.
2. Commits (`git log {{base}}..HEAD`): one per task, Conventional Commits, `<type>(<scope>): <what it does>
   (<ticket>)`, the scope the domain or module in kebab case, each subject ending with its ticket key.
3. Python: typed for mypy strict, with no new `Any`, `cast` or `# type: ignore` without its error code and a reason;
   Pydantic v2 idioms (`model_validate`, `model_dump`, `ConfigDict`, `field_validator`, never v1's `.dict()`,
   `parse_obj` or `class Config`); SQLAlchemy 2.0 style (`select()`, `Mapped[...]` with `mapped_column`, never
   `session.query`); `pathlib` over `os.path`; `logging.getLogger(__name__)`, never `print`; names that follow the
   code around them.
4. The layout: a new route, service, schema, model, test or migration sits where the conventions put it, and its name
   follows its neighbours (`<domain>_service.py`, `tests/api/test_<domain>.py`, `<revision>_<slug>.py`).
5. What ruff doesn't catch, since validation runs it: a broad `except Exception` with no reason, a parameter nothing
   uses, a function nothing calls, a constant duplicated from a schema or an enum.
6. Comments and docs: each says what the code does now. A docstring the change made stale, a `docs/features/` doc or
   `openapi.yaml` entry for a changed endpoint it didn't update, a name that reads as something else.

## Checklist

- Commits: one per task, Conventional Commits, the ticket key in each.
- Typed for mypy strict; Pydantic v2 and SQLAlchemy 2.0 idioms.
- Files and names where the conventions put them.
- Nothing ruff misses: no broad except, dead parameter or dead function.
- Comments, docs and `openapi.yaml` current.

## What to report

A finding is something you can point at: the file and line, the input or state that triggers it, and what goes wrong.
Leave out taste, speculation, and another reviewer's question. This is a personal service with one user and one
maintainer: hardening against a caller that doesn't exist, or an input no client sends, is not a finding.

Give each finding a severity: `high` for one that ships broken, wrong or unsafe behaviour, `medium` for one with a
narrow trigger or that will cost the next change, `low` for the rest.

## Coverage

Submit, beside your findings, what you checked: one entry per rule of the conventions the change is subject to, and one entry per checklist item above. Each entry says `what`
you checked, `how` (the files and lines you read, the command you ran and what it printed), and its `status`: `holds`
when it checked out, `finding` when it gave a finding you submit, or `unchecked` when you couldn't check it, with why
in `how`. A checklist item that doesn't apply to this change gets one `holds` entry saying why.

The judge reads your coverage. A review whose coverage leaves out what this change needed checked isn't trusted, and the
pull request waits for a human instead of merging. Nothing to report is a fine answer when your coverage shows why.

## Submit

Submit a one-paragraph summary of what you found through your question, your coverage, and every finding with its
severity, file, a one-line title and its detail.
