#!/usr/bin/env bash
# Governance: code under PLAN_REQUIRED_PATHS may only change when the active work item has an approved plan.md.
. "$(dirname "$0")/_lib.sh"
[ -z "$FILE" ] && exit 0
R="$(rel "$FILE")"
under_any "$R" "$PLAN_REQUIRED_PATHS" || exit 0
SLUG="${SDLC_WORK_ITEM:-$(cat "$ROOT/.sdlc/active" 2>/dev/null | tr -d '[:space:]')}"
[ -z "$SLUG" ] && block "'$R' needs an approved plan, but no active work item is set. Run /sdlc-intent, or ask a human to set .sdlc/active."
PLAN="$ROOT/work/$SLUG/plan.md"
[ -f "$PLAN" ] || block "'$R' needs an approved plan, but work/$SLUG/plan.md does not exist. Run /sdlc-plan first."
STATUS="$(awk '/^---$/{c++; next} c==1 && /^status:/{sub(/^status:[ \t]*/,""); print; exit}' "$PLAN")"
[ "$STATUS" = "approved" ] || block "work/$SLUG/plan.md has status '$STATUS', not 'approved'. A human must approve the plan before implementation starts."
exit 0
