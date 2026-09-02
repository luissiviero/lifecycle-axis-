#!/usr/bin/env bash
# Red line: agents never edit the control plane or secret material.
#
# Two branches:
#   $FILE set   -> Edit/Write/MultiEdit/NotebookEdit: match the declared file_path.
#   $FILE empty -> Bash: extract likely write targets from the command text and match those.
#                  Defect 4: the edit hooks matched only Edit|Write|MultiEdit, so a heredoc
#                  redirect into .sdlc/config.env bypassed every one of them.
#                  Rationale, coverage and limits: knowledge/decisions/bash-write-guard.md.
# Every candidate is canonicalised (canon in _lib.sh) before matching, so `work/../.sdlc/x`,
# a symlink into the control plane, or `cd .sdlc && ... >> config.env` are all seen as writes
# under `.sdlc` (security review, finding 1).
. "$(dirname "$0")/_lib.sh"

check_target() { # check_target <repo-relative canonical path> <where>
  local R="$1" where="$2"
  under_any "$R" "$PROTECTED_PATHS" && block "'$R' is a protected path ($PROTECTED_PATHS)$where. Describe the change you want in the PR body; a human applies it."
  case "$R" in
    .env|.env.*|*.pem|*.key|*.p12|*id_rsa*|*.keystore) block "'$R' looks like secret material. Never write secrets to the repo$where.";;
  esac
}

if [ -n "$FILE" ]; then
  check_target "$(canon "$FILE")" ""
  exit 0
fi

[ -z "$CMD" ] && exit 0
[ "${BASH_WRITE_GUARD:-1}" = 1 ] || exit 0

# Human-only escape hatch: read from the environment that launched Claude Code (captured in
# _lib.sh before the repo config is sourced). Every allow leaves this line in the transcript.
if [ "${SDLC_CONTROL_PLANE_UNLOCK:-}" = 1 ]; then
  printf 'SDLC: control plane unlocked by human env (SDLC_CONTROL_PLANE_UNLOCK=1)\n' >&2
  exit 0
fi

# Commands whose write target lives in a patch body or an inline script rather than on the
# command line. For these the whole command is searched for protected prefixes.
INLINE_WRITE_RE='(^|[;&|[:space:]])(patch|git[[:space:]]+(apply|am)|(python[0-9._]*|node)[[:space:]]+(-c([[:space:]]|$)|-([[:space:]]|$)|<<))'
OPEN_WRITE_RE='open\([[:space:]]*["'"'"'][^"'"'"']+["'"'"'][[:space:]]*,[[:space:]]*["'"'"'][wa]'

# bash_write_targets <command> -- print one candidate write target per line.
# Deliberately over-inclusive: a false positive costs one stderr line, a false negative costs
# the control plane. Candidates that are not paths are simply tested and discarded.
bash_write_targets() {
  local cmd="${1:0:16384}" s t q e n i j k cpos noglob=0
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
      ln)                                         # a symlink into the control plane is a write there
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
    for t in $PROTECTED_PATHS; do
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

# Directories the command changes into: a relative target written after `cd`/`pushd` resolves
# against them, so every candidate is also tested relative to each such directory.
CD_DIRS="$(printf '%s' "${CMD:0:16384}" | grep -Eo '(^|[;&|[:space:]()])(cd|pushd)[[:space:]]+[^[:space:];&|)]+' \
  | sed -E 's/^[^[:alnum:]]*(cd|pushd)[[:space:]]+//' | tr -d '"'"'"'')"

WHERE=" (detected in a Bash command; use the Write tool for normal edits, describe control-plane changes in the PR body)"
while IFS= read -r CAND; do
  check_target "$(canon "$CAND")" "$WHERE"
  while IFS= read -r D; do
    [ -z "$D" ] && continue
    case "$D" in \$*|*'${'*) continue;; esac
    check_target "$(canon "$CAND" "$(canon "$D")")" "$WHERE"
  done <<EOF
$CD_DIRS
EOF
done < <(bash_write_targets "$CMD")
exit 0
