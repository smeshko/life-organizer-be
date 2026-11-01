#!/usr/bin/env bash
# Computes the next semantic version from the Conventional Commits since the last v* tag.
#
#   scripts/version.sh                    print the next version
#   scripts/version.sh --write            set it in pyproject.toml, uv.lock (life-organizer entry) and openapi.yaml
#   scripts/version.sh --notes [<version>]
#                                         print release notes (New / Fixed / Improved) for <last tag>..HEAD, or, given
#                                         a released version, for the range of its tag
#   scripts/version.sh --current          print the last tag's version
#
# Rules per commit: a `!` before the colon or a BREAKING CHANGE footer bumps major; feat bumps minor; fix, perf and
# refactor bump patch; anything else bumps nothing. The highest bump wins. With no bump, the current version is printed.
# Exit codes: 0 ok, 2 usage, 3 no v* tag (the hint on stderr says how to create the baseline).
set -uo pipefail

cd "$(git rev-parse --show-toplevel)" || exit 2

mode=next
notes_version=''
while [ $# -gt 0 ]; do
  case "$1" in
    --write) mode=write; shift ;;
    --current) mode=current; shift ;;
    --notes)
      mode=notes
      shift
      if [ $# -gt 0 ] && [ "${1#--}" = "$1" ]; then notes_version=$1; shift; fi
      ;;
    *) echo "version: unknown argument $1" >&2; exit 2 ;;
  esac
done

last_tag() { git describe --tags --abbrev=0 --match 'v[0-9]*' "${1:-HEAD}" 2>/dev/null; }

pattern='^[a-z]+(\([^)]*\))?!?: '

# major|minor|patch|none for one commit.
bump_of() {
  local subject body
  subject=$(git log -1 --format=%s "$1")
  body=$(git log -1 --format=%b "$1")
  [[ $subject =~ $pattern ]] || { echo none; return; }
  if [[ $subject =~ ^[a-z]+(\([^\)]*\))?!: ]] || printf '%s\n' "$body" | grep -qE '^BREAKING[ -]CHANGE: '; then
    echo major
    return
  fi
  case "${subject%%[(:]*}" in
    feat) echo minor ;;
    fix | perf | refactor) echo patch ;;
    *) echo none ;;
  esac
}

next_version() {
  local current=$1 range=$2 level=none sha b
  for sha in $(git rev-list "$range"); do
    b=$(bump_of "$sha")
    case "$b" in
      major) level=major ;;
      minor) [ "$level" = major ] || level=minor ;;
      patch) [ "$level" = none ] && level=patch ;;
    esac
  done
  local major minor patch
  IFS=. read -r major minor patch <<<"$current"
  case "$level" in
    major) echo "$((major + 1)).0.0" ;;
    minor) echo "$major.$((minor + 1)).0" ;;
    patch) echo "$major.$minor.$((patch + 1))" ;;
    *) echo "$current" ;;
  esac
}

# Replace the matching line in a file through a temp file; $1 file, $2 awk program with v set.
edit() {
  local tmp
  tmp=$(mktemp)
  awk -v v="$3" "$2" "$1" >"$tmp" && cat "$tmp" >"$1"
  rm -f "$tmp"
}

write_version() {
  local v=$1
  edit pyproject.toml '!done && /^version = / { print "version = \"" v "\""; done = 1; next } { print }' "$v"
  edit uv.lock 'hit && /^version = / { print "version = \"" v "\""; hit = 0; next }
    { hit = ($0 == "name = \"life-organizer\""); print }' "$v"
  edit openapi.yaml '!done && /^  version: / { print "  version: " v; done = 1; next } { print }' "$v"
}

notes() {
  local range=$1 sha subject desc breaking type new='' fixed='' improved=''
  for sha in $(git rev-list --reverse "$range"); do
    subject=$(git log -1 --format=%s "$sha")
    [ "$(bump_of "$sha")" = none ] && continue
    desc=${subject#*: }
    breaking=''
    [ "$(bump_of "$sha")" = major ] && breaking='**Breaking:** '
    type=${subject%%[(:!]*}
    case "$type" in
      feat) [ -z "$breaking" ] && { new+="- $desc"$'\n'; continue; } ;;
      fix) [ -z "$breaking" ] && { fixed+="- $desc"$'\n'; continue; } ;;
    esac
    improved+="- $breaking$desc"$'\n'
  done
  local out='' section
  for section in "New:$new" "Fixed:$fixed" "Improved:$improved"; do
    [ -n "${section#*:}" ] || continue
    out+="${out:+$'\n'}## ${section%%:*}"$'\n'"${section#*:}"
  done
  printf '%s' "$out"
}

if [ "$mode" = notes ] && [ -n "$notes_version" ]; then
  git rev-parse --verify --quiet "v$notes_version^{commit}" >/dev/null ||
    { echo "version: no tag v$notes_version" >&2; exit 2; }
  prev=$(last_tag "v$notes_version^")
  notes "${prev:+$prev..}v$notes_version"
  exit 0
fi

tag=$(last_tag) || {
  base=${VERSION_BASELINE:-1.0.0}
  echo "version: no v* tag found; tag the baseline first: git tag v$base <commit> && git push origin v$base" >&2
  exit 3
}
current=${tag#v}

case "$mode" in
  current) echo "$current" ;;
  notes) notes "$tag..HEAD" ;;
  write) write_version "$(next_version "$current" "$tag..HEAD")" ;;
  next) next_version "$current" "$tag..HEAD" ;;
esac
