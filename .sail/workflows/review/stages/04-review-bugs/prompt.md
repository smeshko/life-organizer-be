Review this pull request for one question: does the change work on every input and path, not only the ones its tests take? Five other reviewers cover requirements, architecture, tests, security and conventions at the same time, and
validation runs `scripts/gate.sh` beside you: ruff check, ruff format, mypy strict and the unit tests. Stay on
your question.

The change is `git diff {{base}}...HEAD`, its commits are `git log {{base}}..HEAD`, the pull request is described at
`{{brief}}`, and what it should do at `{{requirements}}`. Read past the diff: the code around each change, its callers
and its tests are where most problems hide.

You review only. Don't change any file, and don't run the gate or the tests: validation runs them beside you, and
the tests need no second run. Read the code instead, with `git grep`, the Read tool and `sed -n`.

## Method

1. For each function, route and query the change adds or changes, list its inputs and the states it meets: empty,
   missing, `None`, at a boundary (zero, negative, an amount with many decimals, the month's first and last day, a
   naive versus an aware datetime), an enum value the code doesn't know, a duplicated request, Claude returning
   malformed JSON or an unexpected category, and each dependency raising. Trace each through the new code to what it
   returns, what it writes, and what the client receives.
2. Follow each changed function's callers (`git grep`): a new exception, a new `None`, a changed return or a changed
   order must be handled where it lands.
3. Walk every error path: each `await`, database call and Claude call. What does the client receive when it fails: a
   4xx with a useful detail, a 500, a 200 with partial data? A swallowed exception, a bare `except`, an
   `HTTPException` caught by the `except` around it, or a failure logged and then reported as success, are findings.
4. Check the async SQLAlchemy sessions and transactions: each session opened with `async with` and closed; commit on
   success and rollback on failure; writes that must land together in one transaction; every `AsyncSession` call
   awaited; no lazy-loaded relationship read after its session closed; no object carried from one session into
   another; no blocking call (sync I/O, `time.sleep`, a sync client) inside an async route.
5. Check numbers, dates and money: `Decimal` versus `float`, currency conversion and rounding, a sum over an empty
   list, a division by zero, pagination at its edges (page zero, the last page, a size over the limit), and date
   ranges that are inclusive where they should be.
6. Check for performance cliffs: a query per row (N+1), an unbounded query with no limit, a Claude call per item, a
   whole table loaded to count or filter it in Python.

## Checklist

- Every changed function: its inputs traced, its callers checked, its error paths walked.
- Sessions closed, transactions committed or rolled back, every database call awaited.
- No blocking call in async code.
- Numbers, dates, money and pagination correct at their edges.
- Performance on the largest input the change can meet.

## What to report

A finding is something you can point at: the file and line, the input or state that triggers it, and what goes wrong.
Leave out taste, speculation, and another reviewer's question. This is a personal service with one user and one
maintainer: hardening against a caller that doesn't exist, or an input no client sends, is not a finding.

Give each finding a severity: `high` for one that ships broken, wrong or unsafe behaviour, `medium` for one with a
narrow trigger or that will cost the next change, `low` for the rest.

## Coverage

Submit, beside your findings, what you checked: one entry per function, route or query the change adds or changes, and one entry per checklist item above. Each entry says `what`
you checked, `how` (the files and lines you read, the command you ran and what it printed), and its `status`: `holds`
when it checked out, `finding` when it gave a finding you submit, or `unchecked` when you couldn't check it, with why
in `how`. A checklist item that doesn't apply to this change gets one `holds` entry saying why.

The judge reads your coverage. A review whose coverage leaves out what this change needed checked isn't trusted, and the
pull request waits for a human instead of merging. Nothing to report is a fine answer when your coverage shows why.

## Submit

Submit a one-paragraph summary of what you found through your question, your coverage, and every finding with its
severity, file, a one-line title and its detail.
