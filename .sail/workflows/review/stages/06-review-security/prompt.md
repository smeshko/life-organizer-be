Review this pull request for one question: can untrusted input, a widened permission or a leaked secret turn the change against its user? Five other reviewers cover requirements, architecture, bugs, tests and conventions at the same time, and
validation runs `scripts/gate.sh` beside you: ruff check, ruff format, mypy strict and the unit tests. Stay on
your question.

The change is `git diff {{base}}...HEAD`, its commits are `git log {{base}}..HEAD`, the pull request is described at
`{{brief}}`, and what it should do at `{{requirements}}`. Read past the diff: the code around each change, its callers
and its tests are where most problems hide.

You review only. Don't change any file, and don't run the gate or the tests: validation runs them beside you, and
the tests need no second run. Read the code instead, with `git grep`, the Read tool and `sed -n`.

## Method

1. Find where untrusted input enters the change: request bodies, path and query parameters, uploaded files
   (`UploadFile`: its size and content type), and the text Claude returns, which derives from user input and can be
   steered by it. Check each is validated by a Pydantic schema or an enum before it is stored or acted on, and never
   built unchecked into SQL (`text()` with an f-string), a file path, a shell command, or a request to another host.
2. For each route the change adds or changes: it sits on a router `main.py` includes with the `verify_api_key`
   dependency (`auth.py`), unless it is public by intent like `/health`, and nothing in the change makes a protected
   route public. The CORS origins in `config.py` are not widened.
3. For each route that calls Claude: it carries a `@limiter.limit(...)` from `rate_limit.py` as its neighbours do, and
   takes the `request: Request` parameter slowapi needs to apply it.
4. For each secret (the API key, the Anthropic key, the database URL, a user's data): it never reaches a log line, an
   error response, an exception message the client receives, or a committed file (`config/`, `alembic.ini`,
   `docker-compose.yml`, a test). Settings come from the environment through `config.py`: code that reads `.env`
   directly, or logs the settings, is a finding. A 500 must not return a stack trace.
5. For each response the change adds or changes: it returns only the fields its schema declares, and an error's
   `detail` names the problem without echoing internals.
6. For each dependency the change adds or bumps (`pyproject.toml`): who publishes it, and what it reaches.
7. For a change under `.sail/` or `scripts/`: each permission the least its step needs, no command built from
   untrusted text, and no secret printed.

## Checklist

- Untrusted input, Claude's replies among it, validated before use, and never built into SQL, a path or a command.
- Every protected route behind `verify_api_key`, and CORS not widened.
- Every Claude-calling route rate limited.
- No secret or user data reaches a log, a response or a committed file; no `.env` read.
- New dependencies vetted.

## What to report

A finding is something you can point at: the file and line, the input or state that triggers it, and what goes wrong.
Leave out taste, speculation, and another reviewer's question. This is a personal service with one user and one
maintainer: hardening against a caller that doesn't exist, or an input no client sends, is not a finding.

Give each finding a severity: `high` for one that ships broken, wrong or unsafe behaviour, `medium` for one with a
narrow trigger or that will cost the next change, `low` for the rest.

## Coverage

Submit, beside your findings, what you checked: one entry per place untrusted input enters the change, per route, secret or dependency it adds or changes, and one entry per checklist item above. Each entry says `what`
you checked, `how` (the files and lines you read, the command you ran and what it printed), and its `status`: `holds`
when it checked out, `finding` when it gave a finding you submit, or `unchecked` when you couldn't check it, with why
in `how`. A checklist item that doesn't apply to this change gets one `holds` entry saying why.

The judge reads your coverage. A review whose coverage leaves out what this change needed checked isn't trusted, and the
pull request waits for a human instead of merging. Nothing to report is a fine answer when your coverage shows why.

## Submit

Submit a one-paragraph summary of what you found through your question, your coverage, and every finding with its
severity, file, a one-line title and its detail.
