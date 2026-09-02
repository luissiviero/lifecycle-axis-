#!/usr/bin/env bash
# Shared helpers for hooks. Hooks read one JSON object on stdin (Claude Code hook input).
# Exit 0 = allow, exit 2 = block (stderr is shown to the agent), JSON on stdout for "ask".
ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
# shellcheck disable=SC1091
[ -f "$ROOT/.sdlc/config.env" ] && . "$ROOT/.sdlc/config.env"
INPUT="$(cat)"
TOOL="$(printf '%s' "$INPUT" | jq -r '.tool_name // empty')"
FILE="$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty')"
CMD="$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')"
# Path relative to repo root, for matching.
rel() { local p="$1"; p="${p#"$ROOT"/}"; printf '%s' "${p#./}"; }
under_any() { # under_any <relpath> <space-separated prefixes>
  local p="$1" prefix; for prefix in $2; do
    case "$p" in "$prefix"|"$prefix"/*) return 0;; esac; done; return 1; }
block() { printf 'SDLC hook blocked this action: %s\n' "$1" >&2; exit 2; }
ask()   { jq -n --arg r "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"ask",permissionDecisionReason:$r}}'; exit 0; }
