Review this pull request for one question: does the change do what its requirements ask, all of it and nothing more? Five other reviewers cover architecture, bugs, tests, security and conventions at the same time, and
validation runs `scripts/gate.sh` beside you: ruff check, ruff format, mypy strict and the unit tests. Stay on
your question.

The change is `git diff {{base}}...HEAD`, its commits are `git log {{base}}..HEAD`, the pull request is described at
`{{brief}}`, and what it should do at `{{requirements}}`. Read past the diff: the code around each change, its callers
and its tests are where most problems hide.

You review only. Don't change any file, and don't run the gate or the tests: validation runs them beside you, and
the tests need no second run. Read the code instead, with `git grep`, the Read tool and `sed -n`.

## Method

1. Read the requirements end to end and list every acceptance criterion and every constraint they state. A pull request
   with no ticket takes them from its description. A ticket that is an epic phase points at its epic file under
   `docs/artifacts/epics/`: its acceptance criteria are there.
2. For each criterion, find the code that meets it and the test that proves it. Read the test: it must exercise the
   criterion's own input and assert its own outcome (the response's status code and body, the service's return value,
   the row it adds), not a neighbouring path that happens to pass.
3. For a criterion about what a client receives, follow the route to its response model: the status code, the field
   names and types, the JSON shape, and the entry in `openapi.yaml`, which the iOS and web clients read.
4. For each constraint (a limit, a format, a term, an endpoint not to change), check the change keeps it.
5. Read the diff for what the requirements didn't ask for: behaviour added, a default changed, an endpoint or a
   response touched, a file changed that no criterion needs.
6. Read the pull request's description against the diff: what it says the change does is what the change does.

## Checklist

- Every acceptance criterion: met in the code, and proven by a test of its own.
- Every stated constraint: kept.
- Nothing beyond the requirements: no behaviour, option, default or endpoint they didn't ask for.
- The description matches the diff.

## What to report

A finding is something you can point at: the file and line, the input or state that triggers it, and what goes wrong.
Leave out taste, speculation, and another reviewer's question. This is a personal service with one user and one
maintainer: hardening against a caller that doesn't exist, or an input no client sends, is not a finding.

Give each finding a severity: `high` for one that ships broken, wrong or unsafe behaviour, `medium` for one with a
narrow trigger or that will cost the next change, `low` for the rest.

## Coverage

Submit, beside your findings, what you checked: one entry per acceptance criterion and per stated constraint, and one entry per checklist item above. Each entry says `what`
you checked, `how` (the files and lines you read, the command you ran and what it printed), and its `status`: `holds`
when it checked out, `finding` when it gave a finding you submit, or `unchecked` when you couldn't check it, with why
in `how`. A checklist item that doesn't apply to this change gets one `holds` entry saying why.

The judge reads your coverage. A review whose coverage leaves out what this change needed checked isn't trusted, and the
pull request waits for a human instead of merging. Nothing to report is a fine answer when your coverage shows why.

## Submit

Submit a one-paragraph summary of what you found through your question, your coverage, and every finding with its
severity, file, a one-line title and its detail.
