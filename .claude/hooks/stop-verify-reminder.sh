#!/usr/bin/env bash
# Soft nudge at end of turn: if code changed under a plan-required path and
# verify.sh was not run since, say so.
. "$(dirname "$0")/_lib.sh"
# Avoid loops: Claude Code sets stop_hook_active when a Stop hook already continued the turn.
printf '%s' "$INPUT" | jq -e '.stop_hook_active == true' >/dev/null 2>&1 && exit 0
[ -z "$PLAN_REQUIRED_PATHS" ] && exit 0
git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0
STAMP="$ROOT/.sdlc/.last-verify"
re="^(.M|M.|A.|\?\?) ($(printf '%s' "$PLAN_REQUIRED_PATHS" | tr ' ' '|'))/"
porcelain="$(git -C "$ROOT" status --porcelain 2>/dev/null)"
nudge=0
if printf '%s\n' "$porcelain" | grep -Eq "$re"; then
  if [ ! -f "$STAMP" ]; then
    nudge=1
  else
    for p in $PLAN_REQUIRED_PATHS; do
      [ -d "$ROOT/$p" ] || continue
      if [ -n "$(find "$ROOT/$p" -newer "$STAMP" -type f -print -quit 2>/dev/null)" ]; then
        nudge=1
        break
      fi
    done
  fi
fi
if [ "$nudge" = 1 ]; then
  jq -n '{decision:"block",reason:"Code changed since scripts/verify.sh last passed. Run scripts/verify.sh and report its last line before finishing."}'
fi
exit 0
