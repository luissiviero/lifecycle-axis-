#!/usr/bin/env bash
# Feedback-loop protection (Test play): during a fix task the agent may not weaken the check on the code.
# Active when the active work item's plan.md has `kind: fix`.
#
# Two branches, like protect-paths.sh:
#   $FILE set   -> Edit/Write/MultiEdit/NotebookEdit: check the declared file_path.
#   $FILE empty -> Bash: check every likely write target of the command (bash_write_candidates in
#                  _lib.sh), so `sed -i` on a test file is refused like an Edit would be
#                  (roadmap item 17; knowledge/decisions/self-hooks-on.md). BASH_WRITE_GUARD=0 in
#                  .sdlc/config.env switches the Bash branch off, as it does for protect-paths.sh.
. "$(dirname "$0")/_lib.sh"
SLUG="${SDLC_WORK_ITEM:-$(cat "$ROOT/.sdlc/active" 2>/dev/null | tr -d '[:space:]')}"
PLAN="$ROOT/work/$SLUG/plan.md"
[ -f "$PLAN" ] || exit 0
KIND="$(awk '/^---$/{c++; next} c==1 && /^kind:/{sub(/^kind:[ \t]*/,""); print; exit}' "$PLAN")"
[ "$KIND" = "fix" ] || exit 0

check_test_file() { # check_test_file <repo-relative canonical path> <where>
  local R="$1" where="$2" g
  for g in $TEST_FILE_GLOBS; do
    # shellcheck disable=SC2254
    case "$R" in $g|*/$g) block "'$R' is a test file and work/$SLUG/plan.md is kind: fix$where. Fix the code, not the test. If the test itself is wrong, say so and stop; a human changes it.";;
    esac
  done
}

if [ -n "$FILE" ]; then
  check_test_file "$(rel "$FILE")" ""
  exit 0
fi

[ -z "$CMD" ] && exit 0
[ "${BASH_WRITE_GUARD:-1}" = 1 ] || exit 0

WHERE=" (write detected in a Bash command)"
while IFS= read -r CAND; do
  [ -z "$CAND" ] && continue
  check_test_file "$CAND" "$WHERE"
done < <(bash_write_candidates "$CMD" "")
exit 0
