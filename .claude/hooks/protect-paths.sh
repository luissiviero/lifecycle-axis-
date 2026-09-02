#!/usr/bin/env bash
# Red line: agents never edit the control plane or secret material.
#
# Two branches:
#   $FILE set   -> Edit/Write/MultiEdit/NotebookEdit: match the declared file_path.
#   $FILE empty -> Bash: extract likely write targets from the command text and match those
#                  (bash_write_candidates in _lib.sh). Defect 4: the edit hooks matched only
#                  Edit|Write|MultiEdit, so a heredoc redirect into .sdlc/config.env bypassed
#                  every one of them. Rationale, coverage and limits:
#                  knowledge/decisions/bash-write-guard.md.
# Every candidate is canonicalised (canon in _lib.sh) before matching, so `work/../.sdlc/x`,
# a symlink into the control plane, or `cd .sdlc && ... >> config.env` are all seen as writes
# under `.sdlc` (security review, finding 1).
#
# Human-only unlock: SDLC_CONTROL_PLANE_UNLOCK=1 in the environment that launched Claude Code
# (captured in _lib.sh before the repo config is sourced, so a line planted in .sdlc/config.env
# cannot grant it) lets writes under PROTECTED_PATHS through on BOTH branches, one audit line per
# write on stderr. It never lifts the secret-material check (knowledge/decisions/self-hooks-on.md).
. "$(dirname "$0")/_lib.sh"

check_target() { # check_target <repo-relative canonical path> <where>
  local R="$1" where="$2"
  if under_any "$R" "$PROTECTED_PATHS"; then
    if [ "${SDLC_CONTROL_PLANE_UNLOCK:-}" = 1 ]; then
      printf "SDLC: control plane unlocked by human env (SDLC_CONTROL_PLANE_UNLOCK=1): writing '%s'\n" "$R" >&2
    else
      block "'$R' is a protected path ($PROTECTED_PATHS)$where. Describe the change you want in the PR body; a human applies it."
    fi
  fi
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

WHERE=" (detected in a Bash command; use the Write tool for normal edits, describe control-plane changes in the PR body)"
while IFS= read -r CAND; do
  [ -z "$CAND" ] && continue
  check_target "$CAND" "$WHERE"
done < <(bash_write_candidates "$CMD" "$PROTECTED_PATHS")
exit 0
