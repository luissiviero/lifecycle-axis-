#!/usr/bin/env bash
# Shared helpers for hooks. Hooks read one JSON object on stdin (Claude Code hook input).
# Exit 0 = allow, exit 2 = block (stderr is shown to the agent), JSON on stdout for "ask".
# Every block, ask and control-plane unlock is also appended to .sdlc/hook-decisions.log
# (git-ignored TSV, one line per decision; log_decision below), because stderr from an exit-0
# hook never reaches the transcript (work/control-plane-visibility).
#
# Human-only switches are captured from the process environment BEFORE the repo config is
# sourced, so a line planted in .sdlc/config.env can never grant them (security review,
# findings 1 and 2). A command an agent runs sets variables in its own shell, never in this
# hook process's environment.
_ENV_UNLOCK="${SDLC_CONTROL_PLANE_UNLOCK:-}"
_ENV_RELEASE="${RELEASE_APPROVAL:-}"
_ENV_UNATTENDED="${SDLC_UNATTENDED:-}"
ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
# Windows: Claude Code and Gemini CLI both hand the hook `C:\repo` and `C:\repo\src\x.ts`. Fold
# backslashes to slashes here and treat a drive-letter prefix as absolute in canon(); before this
# every such path was taken as relative, landed outside ROOT and was silently allowed
# (knowledge/decisions/gemini-hooks.md). winpath() gives one spelling for ROOT and every
# candidate (cygpath exists only on MSYS/Cygwin; elsewhere it is a no-op).
# The pattern is `/*`, not `/[a-z]/*`: MSYS resolves a symlink into its own POSIX namespace
# using the shortest mount, so realpath returns `/tmp/x/.sdlc` -- not `/c/users/.../.sdlc` --
# for a repo under a named mount. `/[a-z]/*` did not match that, the path stayed POSIX while
# ROOT was `C:/...`, the prefix test said "outside the repo", and a write through a symlink
# into .sdlc was allowed. Found by running the symlink test with Windows Developer Mode on.
winpath() { case "$1" in [A-Za-z]:/*|/*) cygpath -m -- "$1" 2>/dev/null || printf '%s' "$1";; *) printf '%s' "$1";; esac; }
ROOT="${ROOT//\\//}"
ROOT="$(realpath -m -- "$ROOT" 2>/dev/null || printf '%s' "$ROOT")"
ROOT="$(winpath "$ROOT")"
# shellcheck disable=SC1091
[ -f "$ROOT/.sdlc/config.env" ] && . "$ROOT/.sdlc/config.env"
SDLC_CONTROL_PLANE_UNLOCK="$_ENV_UNLOCK"
RELEASE_APPROVAL="$_ENV_RELEASE"
SDLC_UNATTENDED="$_ENV_UNATTENDED"
INPUT="$(cat)"
# Every decision below reads the input with jq. Without jq the fields come back empty and every
# hook would allow blindly, so a gating hook fails closed instead; the advisory hooks stay quiet
# so a missing tool can never wedge the end of a turn. On Windows, winget installs jq into a
# directory the hook process often does not have on PATH, so look there before giving up.
if ! command -v jq >/dev/null 2>&1 && [ -n "${LOCALAPPDATA:-}" ]; then
  for _d in "${LOCALAPPDATA//\\//}"/Microsoft/WinGet/Packages/jqlang.jq_*; do
    [ -x "$_d/jq.exe" ] && PATH="$(cygpath -u -- "$_d"):$PATH" && break
  done
fi
if ! command -v jq >/dev/null 2>&1; then
  case "$0" in
    *stop-verify-reminder.sh|*post-edit-format.sh) exit 0;;
    *) printf 'SDLC hook blocked this action: jq is not on PATH, so %s cannot read its input; refusing rather than allowing blind. Install jq (https://jqlang.org) or add it to PATH, then retry.\n' "$(basename "$0")" >&2; exit 2;;
  esac
fi
TOOL="$(printf '%s' "$INPUT" | jq -r '.tool_name // empty')"
FILE="$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')"
CMD="$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')"
# cwd is the session's working directory and session_id its correlation id (both Claude Code
# hook-input fields; Gemini sends neither, so both may be empty). Backslashes fold like ROOT.
{ IFS= read -r CWD; IFS= read -r SESSION_ID; } < <(printf '%s' "$INPUT" | jq -r '(.cwd // ""), (.session_id // "")')
CWD="${CWD//\\//}"
# canon <path> [<dir>] -> repo-relative canonical path with `..`, `.` and symlinks resolved, or
# the absolute path when it lies outside ROOT. <dir> is the directory the path is relative to
# (a `cd` target inside a Bash command); default: the repo root. Prefix matching on anything
# less than a canonical path is bypassable (security review, finding 1).
canon() {
  local p="${1//\\//}" base="${2:-}" abs
  case "$p" in
    /*|[A-Za-z]:/*) abs="$p";;
    *) case "$base" in
         /*|[A-Za-z]:/*) abs="$base/$p";;
         '') abs="$ROOT/$p";;
         *)  abs="$ROOT/$base/$p";;
       esac;;
  esac
  abs="$(realpath -m -- "$abs" 2>/dev/null)" \
    || abs="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$abs" 2>/dev/null || printf '%s' "$abs")"
  abs="$(winpath "$abs")"
  case "$abs" in
    "$ROOT") printf '.';;
    "$ROOT"/*) printf '%s' "${abs#"$ROOT"/}";;
    *) printf '%s' "$abs";;
  esac
}
# Path relative to repo root, for matching. A relative file_path is relative to the session's
# cwd when the input carries one, else to the repo root.
rel() { canon "$1" "${CWD:-}"; }
under_any() { # under_any <relpath> <space-separated prefixes>
  local p="$1" prefix; for prefix in $2; do
    case "$p" in "$prefix"|"$prefix"/*) return 0;; esac; done; return 1; }
# Decision log: one tab-separated line per block, ask or unlock -- UTC time, verdict, hook,
# tool, session id, detail. Written by the hook process, never by a tool call (the path is on
# protect-paths.sh's never-unlock list). A failed append (no .sdlc/, read-only, a directory in
# the way) is swallowed: the log never changes a verdict or an exit code.
DECISION_LOG="$ROOT/.sdlc/hook-decisions.log"
log_decision() {  # <verdict> <detail>; never fails the hook
  { printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" "$(basename "$0")" "${TOOL:-?}" "${SESSION_ID:-?}" "$2" >> "$DECISION_LOG"; } 2>/dev/null || true
}
block() { log_decision block "$1"; printf 'SDLC hook blocked this action: %s\n' "$1" >&2; exit 2; }
ask()   { log_decision ask "$1"; jq -n --arg r "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"ask",permissionDecisionReason:$r}}'; exit 0; }

# ---------------------------------------------------------------------------------------------
# Artifact and approver readers, shared by the gates that read work/<slug>/*.md and
# .sdlc/approvers.yaml (approval gate, release gate). awk, not python: python3 may be the Store
# stub on Windows, and scripts/check_artifact_chain.py runs git at import time.
# fm_value <file|-> <key> [any] -> the key's value with CR, a trailing ` # comment` and matching
# quotes stripped, casefolded. Without `any` only the leading front-matter block is read; with it
# the whole text is, which is what an Edit's new_string (no `---`) needs.
fm_value() {
  awk -v k="$2" -v any="${3:-}" '
    { sub(/\r$/, "") }
    !any && /^---[[:space:]]*$/ { c++; if (c == 2) exit; next }
    (any || c == 1) && index($0, k ":") == 1 {
      v = substr($0, length(k) + 2)
      sub(/^[[:space:]]+/, "", v); sub(/[[:space:]]+#.*$/, "", v); if (v ~ /^#/) v = ""
      sub(/[[:space:]]+$/, "", v)
      if (length(v) >= 2 && substr(v, 1, 1) == substr(v, length(v), 1) && (substr(v, 1, 1) == "\"" || substr(v, 1, 1) == "\047")) v = substr(v, 2, length(v) - 2)
      print tolower(v); exit }' "$1" 2>/dev/null
}
# artifact_role <artifact> -> the role under `artifacts:` in APPROVERS_FILE (empty when unlisted).
artifact_role() {
  awk -v a="$1" '{ sub(/\r$/, "") } /^[A-Za-z]/ { top = $0; sub(/:.*/, "", top) }
    top == "artifacts" && index($0, "  " a ":") == 1 { v = $0; sub(/^[^:]*:[[:space:]]*/, "", v); sub(/[[:space:]]*#.*$/, "", v); print v; exit }' \
    "$ROOT/${APPROVERS_FILE:-.sdlc/approvers.yaml}" 2>/dev/null
}
# approver_has_role <handle> <role> -> 0 when the handle is listed under roles.<role> and not
# under never-approve; a missing file or an empty handle fails closed (1).
approver_has_role() {
  local f="$ROOT/${APPROVERS_FILE:-.sdlc/approvers.yaml}" h="$1"
  h="${h//\"/}"; h="${h//\'/}"; h="${h#"${h%%[![:space:]]*}"}"; h="${h%%[[:space:]]*}"; h="${h#@}"; h="${h,,}"
  [ -n "$h" ] && [ -f "$f" ] || return 1
  awk -v role="$2" -v h="$h" '
    function norm(x) { gsub(/^[[:space:]]+|[[:space:]]+$/, "", x); gsub(/^["\047]|["\047]$/, "", x); sub(/^@/, "", x); return tolower(x) }
    function has(list,   n, a, i) { sub(/^[[:space:]]*\[/, "", list); sub(/\][[:space:]]*(#.*)?$/, "", list)
      n = split(list, a, ","); for (i = 1; i <= n; i++) if (norm(a[i]) == h) return 1; return 0 }
    { sub(/\r$/, "") }
    /^[A-Za-z]/ { top = $0; sub(/:.*/, "", top) }
    /^never-approve:/ { v = $0; sub(/^never-approve:/, "", v); if (has(v)) bad = 1 }
    top == "roles" && index($0, "  " role ":") == 1 { v = $0; sub(/^[^:]*:/, "", v); if (has(v)) ok = 1 }
    END { exit (ok && !bad) ? 0 : 1 }' "$f"
}

# ---------------------------------------------------------------------------------------------
# Bash write-target extraction, shared by protect-paths.sh, require-plan.sh and protect-tests.sh.
# A Bash call carries no file_path, so each of those hooks derives the likely write targets from
# the command text instead. Rationale, coverage and limits: knowledge/decisions/bash-write-guard.md
# (protected paths) and knowledge/decisions/self-hooks-on.md (plan-required and test paths).
#
# Commands whose write target lives in a patch body or an inline script rather than on the
# command line. For these the whole command is searched for the prefixes the caller guards.
INLINE_WRITE_RE='(^|[;&|[:space:]])(patch|git[[:space:]]+(apply|am)|(python[0-9._]*|node)[[:space:]]+(-c([[:space:]]|$)|-([[:space:]]|$)|<<))'
OPEN_WRITE_RE='open\([[:space:]]*["'"'"'][^"'"'"']+["'"'"'][[:space:]]*,[[:space:]]*["'"'"'][wa]'

# bash_write_targets <command> [<prefixes>] -- print one candidate write target per line.
# <prefixes> (default: PROTECTED_PATHS) are the path prefixes reported when the command is a
# patch or an inline interpreter script that names one of them. Deliberately over-inclusive: a
# false positive costs one stderr line, a false negative costs the guarded path. Candidates that
# are not paths are simply tested by the caller and discarded.
bash_write_targets() {
  local cmd="${1:0:16384}" prefixes="${2-$PROTECTED_PATHS}" s t q e n i j k cpos noglob=0
  local -a toks=() out=()

  # 1. Redirections. Neutralise the descriptor forms first, so `2>&1`, `>&2` and `&>log` can
  #    never look like a file write, then take the word after each surviving `>` or `>>`.
  s="${cmd//>&/ }"; s="${s//2>/ }"; s="${s//&>/ }"
  while IFS= read -r t; do
    t="${t#*>}"; t="${t#>}"; t="${t#"${t%%[![:space:]]*}"}"
    out+=("$t")
  done < <(printf '%s' "$s" | grep -Eo '>>?[[:space:]]*[^[:space:]|;&<>()]+')

  # 2. Command-position rules. Tokenise on whitespace with globbing off: no subshell and no
  #    process per token. This is a heuristic, not a shell parser.
  case "$-" in *f*) noglob=1;; *) set -f;; esac
  # shellcheck disable=SC2206
  toks=( $cmd )
  [ "$noglob" = 1 ] || set +f
  n=${#toks[@]}; i=0; cpos=1
  while [ "$i" -lt "$n" ]; do
    t="${toks[i]}"
    case "$t" in
      '|'|'||'|';'|'&&'|'&'|'('|'{'|'!') cpos=1; i=$((i+1)); continue;;
    esac
    if [ "$cpos" != 1 ]; then i=$((i+1)); continue; fi
    case "$t" in                                  # prefixes that keep command position
      sudo|env|command|nohup|time|xargs|*=*) i=$((i+1)); continue;;
    esac
    cpos=0
    e=$((i+1))                                    # end of this command's argument list
    while [ "$e" -lt "$n" ]; do
      case "${toks[e]}" in '|'|'||'|';'|'&&'|'&') break;; esac
      e=$((e+1))
    done
    case "$t" in
      tee)                                        # tee [-a] <paths...>
        for ((j=i+1; j<e; j++)); do
          case "${toks[j]}" in -*|'<'*|'>'*) continue;; esac
          out+=("${toks[j]}")
        done ;;
      dd)                                         # dd of=<path>
        for ((j=i+1; j<e; j++)); do
          case "${toks[j]}" in of=*) out+=("${toks[j]#of=}");; esac
        done ;;
      sed|perl)                                   # in-place edit: every non-option argument
        k=0
        for ((j=i+1; j<e; j++)); do
          case "${toks[j]}" in -i*) k=1;; esac
        done
        if [ "$k" = 1 ]; then
          for ((j=i+1; j<e; j++)); do
            case "${toks[j]}" in -*|'<'*|'>'*) continue;; esac
            out+=("${toks[j]}")
          done
        fi ;;
      cp|mv|install|rsync)                        # destination is the last argument
        q="${toks[e-1]}"
        case "$q" in -*|'<'*|'>'*) ;; *) out+=("$q");; esac ;;
      ln)                                         # a symlink into a guarded path is a write there
        for ((j=i+1; j<e; j++)); do
          case "${toks[j]}" in -*) continue;; esac
          out+=("${toks[j]}")
        done ;;
      truncate)                                   # truncate [-s N] <path>
        for ((j=i+1; j<e; j++)); do
          case "${toks[j]}" in -*|[0-9]*|'<'*|'>'*) continue;; esac
          out+=("${toks[j]}")
        done ;;
      git)                                        # git checkout|restore <ref> -- <path>
        case "${toks[i+1]}" in
          checkout|restore)
            for ((j=i+2; j<e; j++)); do
              [ "${toks[j]}" = "--" ] || continue
              for ((k=j+1; k<e; k++)); do out+=("${toks[k]}"); done
              break
            done ;;
        esac ;;
    esac
    i=$((i+1))
  done

  # 3. Whole-command rules: patch bodies and inline interpreter scripts (including `python3 -`
  #    reading a heredoc, which has no redirection target at all).
  if printf '%s' "$cmd" | grep -Eq "$INLINE_WRITE_RE"; then
    for t in $prefixes; do
      case "$cmd" in *"$t"*) out+=("$t");; esac
    done
    while IFS= read -r t; do
      t="${t#*open}"; t="${t#*(}"; t="${t#"${t%%[![:space:]]*}"}"
      q="${t:0:1}"; t="${t:1}"; out+=("${t%%"$q"*}")
    done < <(printf '%s' "$cmd" | grep -Eo "$OPEN_WRITE_RE")
  fi

  # 4. Strip quotes and drop what can never be a repo write.
  for t in "${out[@]}"; do
    t="${t%\"}"; t="${t#\"}"; t="${t%\'}"; t="${t#\'}"
    case "$t" in
      ''|/dev/*|\$*|*'${'*) continue;;
    esac
    printf '%s\n' "$t"
  done
}

# bash_write_candidates <command> [<prefixes>] -- every candidate from bash_write_targets as a
# canonical repo-relative path (canon), one per line, each also resolved against every `cd` or
# `pushd` target in the command, so `cd src && echo x > a.ts` is seen as a write to `src/a.ts`.
bash_write_candidates() {
  local cmd="$1" prefixes="${2-$PROTECTED_PATHS}" cand d cd_dirs
  cd_dirs="$(printf '%s' "${cmd:0:16384}" | grep -Eo '(^|[;&|[:space:]()])(cd|pushd)[[:space:]]+[^[:space:];&|)]+' \
    | sed -E 's/^[^[:alnum:]]*(cd|pushd)[[:space:]]+//' | tr -d '"'"'"'')"
  while IFS= read -r cand; do
    [ -z "$cand" ] && continue
    canon "$cand"; printf '\n'
    while IFS= read -r d; do
      [ -z "$d" ] && continue
      case "$d" in \$*|*'${'*) continue;; esac
      canon "$cand" "$(canon "$d")"; printf '\n'
    done <<EOF
$cd_dirs
EOF
  done < <(bash_write_targets "$cmd" "$prefixes")
}
