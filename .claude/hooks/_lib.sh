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
