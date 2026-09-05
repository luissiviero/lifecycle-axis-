#!/usr/bin/env bash
# Governance: code under PLAN_REQUIRED_PATHS may only change when the active work item has an approved plan.md.
# A plan an agent signed under the owner's delegation grant (`status: delegated`) opens the same
# gate, on the policy's terms (work/delegated-mode R-10, D5).
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
  # work/delegated-mode R-10: a delegated plan opens the gate when the policy is on, plan.md is
  # signable there, the item's intent carries the owner's grant, and the signer is an agent the
  # policy lists. Nothing here is the session's to set: the policy and the grant are human commits
  # (.sdlc/delegation.yaml is on protect-paths.sh's never-unlock list).
  if [ "$STATUS" = "delegated" ]; then
    BY="$(fm_value "$PLAN" approved-by)"; POLICY=".sdlc/delegation.yaml"
    delegation_on || block "'$R' needs an approved plan$where: work/$SLUG/plan.md is signed 'delegated', but delegated mode is off ($POLICY is missing or does not say enabled: true). A human must approve the plan."
    artifact_signable plan.md || block "'$R' needs an approved plan$where: work/$SLUG/plan.md is signed 'delegated', but plan.md is not in the signable list of $POLICY. A human must approve the plan."
    [ "$(fm_value "$ROOT/work/$SLUG/intent.md" status)" = "approved" ] || block "'$R' needs an approved plan$where: work/$SLUG/plan.md is signed 'delegated', but work/$SLUG/intent.md is not approved. A grant stands on a human-approved intent."
    [ "$(intent_mode "$SLUG")" = "delegated" ] || block "'$R' needs an approved plan$where: work/$SLUG/plan.md is signed 'delegated', but work/$SLUG/intent.md says mode: $(intent_mode "$SLUG"). Only a human grants delegation, on the intent."
    agent_handle_ok "$BY" || block "'$R' needs an approved plan$where: work/$SLUG/plan.md says approved-by '$BY', who is not an agent listed in $POLICY (or the file is missing). A signature is written by scripts/sign.py under a listed agent handle."
    return 0
  fi
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
