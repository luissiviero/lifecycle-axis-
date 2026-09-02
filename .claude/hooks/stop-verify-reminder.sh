#!/usr/bin/env bash
# Soft nudge at end of turn: if code changed and verify.sh was not run this session, say so.
ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
INPUT="$(cat)"
# Avoid loops: Claude Code sets stop_hook_active when a Stop hook already continued the turn.
printf '%s' "$INPUT" | jq -e '.stop_hook_active == true' >/dev/null 2>&1 && exit 0
STAMP="$ROOT/.sdlc/.last-verify"
if git -C "$ROOT" status --porcelain 2>/dev/null | grep -Eq '^( M|A |M |\?\?) (src|lib|app|services|packages)/'; then
  if [ ! -f "$STAMP" ] || [ -n "$(find "$ROOT" -newer "$STAMP" -path '*/src/*' -o -newer "$STAMP" -path '*/lib/*' 2>/dev/null | head -1)" ]; then
    jq -n '{decision:"block",reason:"Code changed since scripts/verify.sh last passed. Run scripts/verify.sh and report its last line before finishing."}'
    exit 0
  fi
fi
exit 0
