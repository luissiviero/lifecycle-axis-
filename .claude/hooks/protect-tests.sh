#!/usr/bin/env bash
# Feedback-loop protection (Test play): during a fix task the agent may not weaken the check on the code.
# Active when the active work item's plan.md has `kind: fix`.
. "$(dirname "$0")/_lib.sh"
[ -z "$FILE" ] && exit 0
R="$(rel "$FILE")"
SLUG="${SDLC_WORK_ITEM:-$(cat "$ROOT/.sdlc/active" 2>/dev/null | tr -d '[:space:]')}"
PLAN="$ROOT/work/$SLUG/plan.md"
[ -f "$PLAN" ] || exit 0
KIND="$(awk '/^---$/{c++; next} c==1 && /^kind:/{sub(/^kind:[ \t]*/,""); print; exit}' "$PLAN")"
[ "$KIND" = "fix" ] || exit 0
for g in $TEST_FILE_GLOBS; do
  # shellcheck disable=SC2254
  case "$R" in $g|*/$g) block "'$R' is a test file and work/$SLUG/plan.md is kind: fix. Fix the code, not the test. If the test itself is wrong, say so and stop; a human changes it.";;
  esac
done
exit 0
