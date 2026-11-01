# CI

`.github/workflows/ci.yml` runs on pull requests into `staging` and on pushes to it. A new push to a PR cancels its
stale run (concurrency group per PR); pushes to `staging` keep their own group, so none is cancelled. It uses no secrets, so integration tests stay out.

## Jobs

- `gate`: uv 0.8.22, `uv sync --frozen --all-extras`, then `scripts/gate.sh` with `UV_FROZEN=1` so every `uv run`
  uses the committed `uv.lock`.
- `docker`: `docker build .` only. The image's CMD runs `alembic upgrade head`, which needs a database, so the image is
  never run in CI; check `https://org.ivot.dev/health` once production runs the change.
- `release` (pushes to `staging` only, after `gate`): tags and releases the next version, see Releases.

## Reproduce locally

```bash
uv sync --frozen --all-extras && scripts/gate.sh
docker build .
```

`uv.lock` and `.python-version` (3.14) are committed. Change dependencies with `uv add` / `uv lock` and commit the
new lock.

## Require `gate` on `staging`

Run once after the first green run (needs admin rights):

```bash
gh api --method PUT repos/smeshko/life-organizer-be/branches/staging/protection --input - <<'EOF'
{
  "required_status_checks": { "strict": false, "contexts": ["gate"] },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null
}
EOF
gh api repos/smeshko/life-organizer-be/branches/staging/protection/required_status_checks
```

The second command should show `gate` in `contexts`. `PUT` replaces any existing protection on `staging`; when
protection already exists, use this instead:

```bash
gh api --method PATCH repos/smeshko/life-organizer-be/branches/staging/protection/required_status_checks \
  -f strict=false -f 'contexts[]=gate'
```

`strict` is false because PRs are merged one at a time; requiring up-to-date branches would force a rebase for every
merge. The repository is public, so required checks work on the free plan.

## Releases

`scripts/version.sh` computes the next version from the Conventional Commits since the last `v*` tag. A `!` before the
colon or a `BREAKING CHANGE:` footer bumps major, `feat` bumps minor, `fix`, `perf` and `refactor` bump patch; every
other type, and any non-conventional subject, bumps nothing. The highest bump wins. `scripts/test-version.sh` tests
these rules and runs in the gate.

After `gate` passes on a push to `staging`, the `release` job:

1. Skips with a notice when `staging` has moved on since the push (the newer push's run releases everything), when no
   `v*` tag exists, or when nothing bumps (a docs-only merge creates no tag).
2. Runs `scripts/version.sh --write` (`pyproject.toml`, `uv.lock`, `openapi.yaml`), commits `chore(release): vX.Y.Z` as
   `github-actions[bot]`, tags it `vX.Y.Z`, pushes the commit and the tag in one atomic push and creates a GitHub
   Release whose notes are `scripts/version.sh --notes` (New / Fixed / Improved).

The pushes use `GITHUB_TOKEN`, which starts no workflow, so the bump commit triggers no further CI run. The running
service reports the version from package metadata at `/health`.

One-time, by the maintainer: tag the baseline, or the job skips with a notice.

```bash
git tag v1.0.0 <commit> && git push origin v1.0.0
```

`scripts/version.sh --notes <version>` prints the notes of any past release.

If required checks are turned on for `staging` (see above), the release push needs a bypass for the Actions bot, or it
is rejected.
