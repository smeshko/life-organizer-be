#!/usr/bin/env bash
# The close-ticket stage: moves the ticket in $INPUT_TICKETKEY to Done. Its last stdout line is whether it did.
set -uo pipefail
key=$(cat "$INPUT_TICKETKEY")
if err=$(sail port ticket-source update "$key" --state done 2>&1 >/dev/null); then
  printf '{"closed":true,"error":null}\n'
else
  printf 'moving %s to done failed: %s\n' "$key" "$err" >&2
  printf '{"closed":false,"error":%s}\n' "$(printf '%s' "$err" | head -1 | "${SAIL_BUN:-bun}" -e 'process.stdout.write(JSON.stringify(require("fs").readFileSync(0,"utf8")))')"
fi
