#!/usr/bin/env bash
# Governance: code under PLAN_REQUIRED_PATHS may only change when the active work item has an approved plan.md.
#
# Two branches, like protect-paths.sh:
#   $FILE set   -> Edit/Write/MultiEdit/NotebookEdit: check the declared file_path.
#   $FILE empty -> Bash: check every likely write target of the command (bash_write_candidates in
#                  _lib.sh), so a heredoc into src/ needs the same approved plan as an Edit would
#                  (roadmap item 17; knowledge/decisions/self-hooks-on.md). BASH_WRITE_GUARD=0 in
#                  .sdlc/config.env switches the Bash branch off, as it does for protect-paths.sh.
. "$(dirname "$0")/_lib.sh"

check_plan_required() { # check_plan_required <repo-relative canonical path> <where>
  local R="$1" where="$2" SLUG PLAN STATUS
  under_any "$R" "$PLAN_REQUIRED_PATHS" || return 0
  SLUG="${SDLC_WORK_ITEM:-$(cat "$ROOT/.sdlc/active" 2>/dev/null | tr -d '[:space:]')}"
  [ -z "$SLUG" ] && block "'$R' needs an approved plan$where, but no active work item is set. Run /sdlc-intent, or ask a human to set .sdlc/active."
  PLAN="$ROOT/work/$SLUG/plan.md"
  [ -f "$PLAN" ] || block "'$R' needs an approved plan$where, but work/$SLUG/plan.md does not exist. Run /sdlc-plan first."
  STATUS="$(fm_value "$PLAN" status)"   # comment, quotes, capitals and CRLF stripped (_lib.sh)
  [ "$STATUS" = "approved" ] || block "'$R' needs an approved plan$where: work/$SLUG/plan.md has status '$STATUS', not 'approved'. A human must approve the plan before implementation starts."
  # work/approval-gate R-6: the approver must hold the plan's role (artifacts.plan.md in the approvers
  # file) and not sit in never-approve; a missing approvers file fails closed (approver_has_role, _lib.sh).
  BY="$(fm_value "$PLAN" approved-by)"; ROLE="$(artifact_role plan.md)"; ROLE="${ROLE:-tech-lead}"
  approver_has_role "$BY" "$ROLE" || block "'$R' needs an approved plan$where: work/$SLUG/plan.md says approved-by '$BY', who is not a $ROLE in ${APPROVERS_FILE:-.sdlc/approvers.yaml} (or the file is missing). A listed human must approve with scripts/approve.py."
}

if [ -n "$FILE" ]; then
  check_plan_required "$(rel "$FILE")" ""
  exit 0
fi

[ -z "$CMD" ] && exit 0
[ "${BASH_WRITE_GUARD:-1}" = 1 ] || exit 0

WHERE=" (write detected in a Bash command; use the Write tool for normal edits)"
while IFS= read -r CAND; do
  [ -z "$CAND" ] && continue
  check_plan_required "$CAND" "$WHERE"
done < <(bash_write_candidates "$CMD" "$PLAN_REQUIRED_PATHS")
exit 0
