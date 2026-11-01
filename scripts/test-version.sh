#!/usr/bin/env bash
# Tests scripts/version.sh against throwaway git repositories: the bump rules, --write, --notes, --current, the
# no-baseline-tag hint and the usage error. Prints `test-version: <case> passed|FAILED` and exits 1 on any failure.
#
#   scripts/test-version.sh
set -uo pipefail

script=$(cd "$(dirname "$0")" && pwd)/version.sh
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
failed=0
n=0

# A repository with the three versioned files, committed and tagged v1.0.0; leaves the shell inside it.
repo() {
  n=$((n + 1))
  local dir=$tmp/r$n
  mkdir -p "$dir"
  cd "$dir" || exit 2
  git init -q
  printf '[project]\nname = "life-organizer"\nversion = "1.0.0"\n' >pyproject.toml
  printf '[[package]]\nname = "other"\nversion = "9.9.9"\n\n[[package]]\nname = "life-organizer"\nversion = "1.0.0"\nsource = { editable = "." }\n' >uv.lock
  printf 'info:\n  version: 1.0.0\npaths:\n  x:\n    version: 1.0.0\n' >openapi.yaml
  git add .
  commit 'chore: baseline'
  git tag v1.0.0
}

commit() {
  git -c user.name=test -c user.email=test@example.com -c commit.gpgsign=false \
    commit -q --allow-empty ${1:+-m "$1"} ${2:+-m "$2"} || exit 2
}

expect() {
  if [ "$2" = "$3" ]; then
    echo "test-version: $1 passed"
  else
    echo "test-version: $1 FAILED: expected '$2', got '$3'"
    failed=1
  fi
}

bump_case() {
  local name=$1 expected=$2
  shift 2
  repo
  for subject in "$@"; do commit "$subject"; done
  expect "$name" "$expected" "$("$script" 2>/dev/null)"
}

bump_case 'feat bumps minor' 1.1.0 'feat(budget): x'
bump_case 'fix bumps patch' 1.0.1 'fix: x'
bump_case 'perf bumps patch' 1.0.1 'perf: x'
bump_case 'refactor bumps patch' 1.0.1 'refactor: x'
bump_case 'bang bumps major' 2.0.0 'feat!: x'
bump_case 'scoped bang bumps major' 2.0.0 'chore(api)!: x'
bump_case 'feat with fix bumps minor' 1.1.0 'fix: y' 'feat: x'
bump_case 'docs chore ci test bump nothing' 1.0.0 'docs: a' 'chore: b' 'ci: c' 'test: d'
bump_case 'non-conventional subject bumps nothing' 1.0.0 'Deploy updates'
bump_case 'no commits bump nothing' 1.0.0

repo
commit 'fix: x' 'BREAKING CHANGE: y'
expect 'breaking footer bumps major' 2.0.0 "$("$script" 2>/dev/null)"

repo
commit 'feat: x'
git tag v1.1.0
commit 'fix: y'
expect 'only commits after the last tag count' 1.1.1 "$("$script" 2>/dev/null)"

repo
commit 'docs: a'
expect '--current prints the last tag version' 1.0.0 "$("$script" --current 2>/dev/null)"

repo
commit 'feat: x'
"$script" --write 2>/dev/null
expect '--write sets pyproject.toml' 'version = "1.1.0"' "$(grep '^version' pyproject.toml)"
expect '--write sets the life-organizer entry only' '9.9.9 1.1.0' \
  "$(grep '^version' uv.lock | sed 's/version = "\(.*\)"/\1/' | tr '\n' ' ' | sed 's/ $//')"
expect '--write sets info.version only' '1.1.0 1.0.0' \
  "$(grep 'version:' openapi.yaml | sed 's/.*version: //' | tr '\n' ' ' | sed 's/ $//')"

repo
commit 'feat(budget): add export (LIFE-1)'
commit 'fix: stop crash'
commit 'refactor(core): tidy'
commit 'docs: words'
expected=$'## New\n- add export (LIFE-1)\n\n## Fixed\n- stop crash\n\n## Improved\n- tidy'
expect '--notes groups New Fixed Improved' "$expected" "$("$script" --notes 2>/dev/null)"

repo
commit 'feat!: drop v0'
expect '--notes marks breaking commits' $'## Improved\n- **Breaking:** drop v0' "$("$script" --notes 2>/dev/null)"

repo
commit 'feat: first'
git tag v1.1.0
commit 'fix: second'
expect '--notes <version> covers only that tag range' $'## New\n- first' "$("$script" --notes 1.1.0 2>/dev/null)"

n=$((n + 1))
mkdir "$tmp/r$n" && cd "$tmp/r$n" && git init -q && commit 'feat: x'
out=$("$script" 2>&1 >/dev/null)
code=$?
expect 'no tag exits 3' 3 "$code"
case "$out" in *v1.0.0*) echo 'test-version: no tag hint passed' ;; *) echo "test-version: no tag hint FAILED: '$out'"; failed=1 ;; esac

"$script" --bogus >/dev/null 2>&1
expect 'unknown argument exits 2' 2 "$?"

exit "$failed"
