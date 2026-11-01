#!/usr/bin/env bash
# The gate: the one way to verify a change. Runs, in order and each one regardless of the last:
#   ruff check · ruff format --check · mypy src · pytest -m "not integration"
# and exits 1 when any of them failed, 0 when all passed. Ruff checks the Python trees by name (src, tests, alembic):
# this keeps it off docs/, .sail/ and Markdown. uv.lock is committed, so every run resolves the same tool versions.
#
#   scripts/gate.sh                  run every step
#   scripts/gate.sh --base <commit>  skip every step when the change since <commit> (committed, staged, unstaged and
#                                    untracked) touches only docs (docs/, *.md) or .sail/; run every step otherwise
#   scripts/gate.sh --list [--base <commit>]
#                                    print ALL when the gate would run, nothing when it would skip, and exit
#
# Integration tests (marked `integration`, they call the Anthropic API) stay out of the gate. The unit tests run with
# placeholder API_KEY and CLAUDE_API_KEY, so the gate passes in a worktree with no .env and never reaches a real key.
set -uo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root" || exit 2
base=''
list=false
while [ $# -gt 0 ]; do
  case "$1" in
    --base)
      [ $# -ge 2 ] || { echo "gate: --base needs a commit" >&2; exit 2; }
      base=$2
      shift 2
      ;;
    --list) list=true; shift ;;
    *) echo "gate: unknown argument $1" >&2; exit 2 ;;
  esac
done

# ALL when the change since $base touches anything but docs and .sail/, or when there is no base; nothing otherwise.
selection() {
  [ -z "$base" ] && { echo ALL; return; }
  git rev-parse --verify --quiet "$base^{commit}" >/dev/null || { echo "gate: unknown commit $base" >&2; exit 2; }
  local changed
  changed=$(git diff --name-only "$base" HEAD --; git diff --name-only HEAD --; git ls-files --others --exclude-standard)
  if printf '%s\n' "$changed" | grep -v -E '^$|^docs/|^\.sail/|\.md$' >/dev/null; then echo ALL; fi
}

selected=$(selection) || exit $?
if $list; then
  [ -n "$selected" ] && echo "$selected"
  exit 0
fi
if [ -z "$selected" ]; then
  echo "gate: only docs or .sail/ changed since $base; nothing to check"
  exit 0
fi

failed=()
step() {
  local name=$1
  shift
  # On stdout with the step's own output, so a reader of both streams sees each step's output under its line.
  echo "gate: $name"
  if "$@" 2>&1; then echo "gate: $name passed"; else echo "gate: $name FAILED"; failed+=("$name"); fi
}

python=(src tests alembic)
step 'ruff check' uv run ruff check "${python[@]}"
step 'ruff format' uv run ruff format --check "${python[@]}"
step 'mypy' uv run mypy src
step 'pytest' env API_KEY=gate-placeholder CLAUDE_API_KEY=gate-placeholder \
  uv run pytest -m 'not integration' -q -rfE --no-cov -p no:cacheprovider

if [ ${#failed[@]} -gt 0 ]; then
  echo "gate: FAILED: $(IFS=,; echo "${failed[*]}" | sed 's/,/, /g')"
  exit 1
fi
echo "gate: passed: ruff check, ruff format, mypy, pytest"
