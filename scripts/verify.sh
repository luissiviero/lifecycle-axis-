#!/usr/bin/env bash
# One command, one exit code. Agents run this before requesting review; CI runs it on every PR.
set -u
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
# shellcheck disable=SC1091
. "$ROOT/.sdlc/config.env"
fail=0
while IFS= read -r cmd; do
  [ -z "$cmd" ] && continue
  echo "▶ $cmd"
  if bash -c "$cmd"; then echo "  ✔ pass"; else echo "  ✘ FAIL"; fail=1; fi
done <<< "$(printf '%s\n' "$VERIFY_CMDS" | tr ';' '\n')"
shopt -s nullglob
for check in "$ROOT"/scripts/checks/*.sh; do
  [ -x "$check" ] || continue
  echo "▶ $check"
  if bash -c "$check"; then echo "  ✔ pass"; else echo "  ✘ FAIL"; fail=1; fi
done
shopt -u nullglob
if [ "$fail" = 0 ]; then
  touch "$ROOT/.sdlc/.last-verify" 2>/dev/null || true
  echo "VERIFY: PASS ($(git rev-parse --short HEAD 2>/dev/null || echo no-git))"
else
  echo "VERIFY: FAIL"; exit 1
fi
