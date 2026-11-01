# CI

`.github/workflows/ci.yml` runs on pull requests into `staging` and on pushes to it. A new push to a PR cancels its
stale run (concurrency group per PR). It uses no secrets, so integration tests stay out.

## Jobs

- `gate`: uv 0.8.22, `uv sync --frozen --all-extras`, then `scripts/gate.sh` with `UV_FROZEN=1` so every `uv run`
  uses the committed `uv.lock`.
- `docker`: `docker build .` only. The image's CMD runs `alembic upgrade head`, which needs a database, so the image is
  never run in CI; check `/health` on the Railway staging deploy after merge.

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
