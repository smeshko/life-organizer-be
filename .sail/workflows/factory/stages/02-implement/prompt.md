Implement the plan at `{{plan}}`: walk its tasks in order, test first, and make exactly one commit per task. Read the
plan end to end first: its Goal, Scope, Decisions and Acceptance Criteria bound everything you do.

{{#if feedback}}
{{#if feedback.validation}}
## The last pass failed validation

`$STAGE_IN/feedback.json` holds, under `validation`, what validation found: paths left uncommitted, and how
`scripts/gate.sh` ended: the steps that failed (`ruff check`, `ruff format`, `mypy`, `pytest`) with their output, and
each failing test by its node id and message. Your commits from that pass
are on the branch. Fix what it reports first, in commits of their own (`fix(<scope>): …`), then carry on with any task
not yet committed.

{{/if}}
{{#if feedback.tasks}}
## The last pass left tasks unimplemented

Validation passed, but a check of the branch against the plan found tasks it doesn't implement.
`$STAGE_IN/feedback.json` holds, under `tasks`, each task with whether it is implemented and what is missing. Your
commits from that pass are on the branch. Implement each missing task, or the part of it that is missing, the way the
steps below say, in a commit of its own.

{{/if}}
{{/if}}
## For each task, in order

1. Re-read the task's details and the files it lists, so your change fits the code as it is now.
2. **Red** (`impl` tasks): write the task's tests first, and run them to watch each fail on its assertion, not on an
   `ImportError` or `AttributeError`. Give a new function its final signature and a body that returns a wrong value of
   the right type, so the test imports it and reaches its `assert`.
   - One test per acceptance behaviour, plus one per branch that breaks on its own (a boundary, an error path), each
     asserting the exact value. Name it after the behaviour.
   - Every test is non-vacuous: name to yourself the regression it catches, and check that breaking the behaviour
     (revert the change, flip a condition, return a constant) turns it red. No assertion on a mock the test set up
     itself, no expected value computed by the code under test, no loop over an empty collection.
   - Follow the layout and style of the module's existing tests under `tests/` (`tests/api/test_budget.py` for a
     route, `tests/services/test_budget_service.py` for a service): plain pytest functions or classes, async tests
     with no decorator (`asyncio_mode = "auto"`), `unittest.mock` (`AsyncMock`, `MagicMock`, `patch`) for the session
     factory and the Claude client, and the file's own helpers rather than new ones. No test reaches a database or
     the Anthropic API; one that must is marked `@pytest.mark.integration` and stays out of the gate. A behaviour the
     existing tests already cover gets those tests updated.
3. **Green**: change production code until the task's tests pass, and the other tests of the modules you changed.
   **Refactor** with the tests staying green. Never weaken a test to make it pass.
4. **Checklist** tasks are non-code work, such as `uv add <package>` or a config file: run their steps in order.
5. **Verify the acceptance** with the evidence the task names: run the tests and keep the output. Code that compiles or
   looks right is not evidence. Don't commit a task whose acceptance fails.
6. Run tests with placeholder keys, since the settings require them and the workspace has no `.env`:
   `API_KEY=x CLAUDE_API_KEY=x uv run pytest <node id or file> --no-cov -q`. Before each commit, run
   `scripts/gate.sh`: ruff check, ruff format --check, mypy src and every unit test, in under a minute. Fix what it
   reports with `uv run ruff check --fix <paths>` and `uv run ruff format <paths>`, and type every new function: mypy
   runs strict. Validation runs the same gate after the last task.
7. **Commit** the task's tests and code together: stage every path it changed by name (`git add <paths>`, never `-A`
   or `.`), then `git commit -m '<subject>'`, the task's suggested subject, its type or scope changed only if the diff
   demands it, ending with the ticket: `feat({{commit.scope}}): <what it does> ({{commit.ticketKey}})`.

Read files with the Read tool, or `sed -n` for a range, and change them with Edit and Write. A migration is written by
hand under `alembic/versions/`: nothing in this run reaches a database, so `alembic upgrade` and `--autogenerate`
are denied, and `make` with them, since its targets stop the machine's dev server.

Write a scratch file, if you need one, under `$STAGE_OUT`, never in the repository: `rm` and `git clean` are
denied, so a file left there can't be removed, and validation fails while any path is uncommitted. Pushing, `gh` and
network clients are denied too: the workflow's own stages push and open the pull request.

## When something is wrong

- A test that won't pass, or acceptance you can't meet: end the step **blocked**, saying what you tried and what
  failed. Never commit a partial result, and never skip to the next task.
- Tests failing that your change doesn't reach: say so in your notes, naming them, and carry on; validation checks
  them against the base.
- Files that drifted from the plan: follow the code as it is, and say so in your notes.
- Work the plan doesn't list: leave it, and say so in your notes. Don't invent tasks.

## Submit

Submit each task with its commit's sha and the evidence that proves its acceptance: the tests that went red, then
green. Add a short note on anything you did differently from the plan.
