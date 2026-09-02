#!/usr/bin/env bash
# Shared helpers for hooks. Hooks read one JSON object on stdin (Claude Code hook input).
# Exit 0 = allow, exit 2 = block (stderr is shown to the agent), JSON on stdout for "ask".
#
# Human-only switches are captured from the process environment BEFORE the repo config is
# sourced, so a line planted in .sdlc/config.env can never grant them (security review,
# findings 1 and 2). A command an agent runs sets variables in its own shell, never in this
# hook process's environment.
_ENV_UNLOCK="${SDLC_CONTROL_PLANE_UNLOCK:-}"
_ENV_RELEASE="${RELEASE_APPROVAL:-}"
_ENV_UNATTENDED="${SDLC_UNATTENDED:-}"
ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
ROOT="$(realpath -m -- "$ROOT" 2>/dev/null || printf '%s' "$ROOT")"
# shellcheck disable=SC1091
[ -f "$ROOT/.sdlc/config.env" ] && . "$ROOT/.sdlc/config.env"
SDLC_CONTROL_PLANE_UNLOCK="$_ENV_UNLOCK"
RELEASE_APPROVAL="$_ENV_RELEASE"
SDLC_UNATTENDED="$_ENV_UNATTENDED"
INPUT="$(cat)"
TOOL="$(printf '%s' "$INPUT" | jq -r '.tool_name // empty')"
FILE="$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty')"
CMD="$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')"
# canon <path> [<dir>] -> repo-relative canonical path with `..`, `.` and symlinks resolved, or
# the absolute path when it lies outside ROOT. <dir> is the directory the path is relative to
# (a `cd` target inside a Bash command); default: the repo root. Prefix matching on anything
# less than a canonical path is bypassable (security review, finding 1).
canon() {
  local p="$1" base="${2:-}" abs
  case "$p" in
    /*) abs="$p";;
    *) case "$base" in
         /*) abs="$base/$p";;
         '') abs="$ROOT/$p";;
         *)  abs="$ROOT/$base/$p";;
       esac;;
  esac
  abs="$(realpath -m -- "$abs" 2>/dev/null)" \
    || abs="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$abs" 2>/dev/null || printf '%s' "$abs")"
  case "$abs" in
    "$ROOT") printf '.';;
    "$ROOT"/*) printf '%s' "${abs#"$ROOT"/}";;
    *) printf '%s' "$abs";;
  esac
}
# Path relative to repo root, for matching.
rel() { canon "$1"; }
under_any() { # under_any <relpath> <space-separated prefixes>
  local p="$1" prefix; for prefix in $2; do
    case "$p" in "$prefix"|"$prefix"/*) return 0;; esac; done; return 1; }
block() { printf 'SDLC hook blocked this action: %s\n' "$1" >&2; exit 2; }
ask()   { jq -n --arg r "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"ask",permissionDecisionReason:$r}}'; exit 0; }
