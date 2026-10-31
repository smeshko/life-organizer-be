Describe the change on this branch for its pull request into `staging`, from the ticket, the plan at `{{plan}}`, and
the commits (`git log origin/staging..HEAD`).

Write `$STAGE_OUT/pr-body.md`, never a path in the repository, with these sections:

- **Summary**: what changes and why, in two or three sentences, in the API's own terms: the endpoints, the
  budget and meals domains, and what a client sees differently.
- **Changes**: one bullet per commit or group of related commits.
- **Testing**: the tests the plan added and what they prove, and `scripts/gate.sh` passing (ruff, mypy and the unit
  tests). Name any migration, and say it was not run against a database.
- **Follow-ups**: each follow-up you submit, one bullet each, or leave the section out when there is none. Each is
  filed as a ticket once the pull request is open.

End the body with `Closes <ticket key>` on its own line.

Submit the title, a Conventional Commits subject ending with the ticket key in parentheses, and
`$STAGE_OUT/pr-body.md` as the body file.

Submit as `followUps` the work outside this branch that the plan's Out of Scope or the implementation's notes
surfaced, and that is worth a ticket of its own: usually a bug the change exposed. A ticket costs a reader's attention
every time they pass it, and this is a personal app with one user and one maintainer. File one only when doing it
changes something that person would notice: a failure they hit or can reach through a real path, a behaviour they
asked for, or a measured cost. Never file hardening against a misuse no caller makes or an input no path produces, a
tidy-up with no behaviour behind it (a rename, a move, a shared helper, a comment, an unused field), a test for code
with no reported failure, accessibility work, or anything smaller than writing it up. A run files at most two tickets,
bugs first.

Give each a title, a description a reader can act on without this run (the files, what is wrong, why it was left), the
`trigger` (the endpoint and request, or the code path that reaches the problem), and its type: `bug`, `feature` or
`refactoring`. Leave out anything the plan rules out as unwanted, and anything an epic under `docs/artifacts/epics/`
already plans. Submit none when there is none: an empty list is the usual answer.
