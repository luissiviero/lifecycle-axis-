#!/usr/bin/env bash
# Only a human approves. An agent may draft, revise and flip an artifact to in-review, but may
# never set `status: approved|superseded`, `approved-by:` or `approved-on:` on
# work/<slug>/{intent,spec,plan,incident}.md, nor run scripts/approve.py. The human unlock
# (SDLC_CONTROL_PLANE_UNLOCK) never applies here (work/approval-gate; knowledge/decisions/human-only-approvals.md).
#
# Two branches, like protect-paths.sh:
#   $FILE set   -> Edit/Write/MultiEdit/NotebookEdit: the new text's approval fields are compared
#                  with the file's current values; an approval-shaped change is blocked.
#   $FILE empty -> Bash: `approve.py` and any CLAUDECODE unset/reassignment are refused outright;
#                  then, when BASH_WRITE_GUARD is on, every write candidate that is a chain artifact
#                  is checked against the whole command text.
. "$(dirname "$0")/_lib.sh"
ARTIFACT_RE='^work/[^/]+/(intent|spec|plan|incident)\.md$'
APPROVE_PY_RE='(^|[/[:space:]])approve\.py([[:space:]]|$)'
CLAUDECODE_RE='(env[[:space:]]+(-u|--unset)[[:space:]]+CLAUDECODE|unset[[:space:]]+CLAUDECODE|(^|[[:space:];&|])CLAUDECODE=)'
check_approval_fields() {  # <repo-relative path> <new text> <where>
  local R="$1" new="$2" where="$3" ns nb no cs cb co
  printf '%s' "$R" | grep -Eq "$ARTIFACT_RE" || return 0
  ns="$(printf '%s\n' "$new" | fm_value - status any)"
  nb="$(printf '%s\n' "$new" | fm_value - approved-by any)"
  no="$(printf '%s\n' "$new" | fm_value - approved-on any)"
  cs="$(fm_value "$ROOT/$R" status)"; cb="$(fm_value "$ROOT/$R" approved-by)"; co="$(fm_value "$ROOT/$R" approved-on)"
  case "$ns" in approved|superseded) [ "$ns" = "$cs" ] || block "'$R' would become status: $ns$where. Only a human approves: ask them to run scripts/approve.py from their own shell, then wait.";; esac
  [ -n "$nb" ] && [ "$nb" != "$cb" ] && block "'$R' would set approved-by: $nb$where. Only a human sets approved-by."
  [ -n "$no" ] && [ "$no" != "$co" ] && block "'$R' would set approved-on: $no$where. Only a human sets approved-on."
  return 0
}
if [ -n "$FILE" ]; then
  NEW="$(printf '%s' "$INPUT" | jq -r '(.tool_input.content // "") + "\n" + (.tool_input.new_string // "") + "\n" + ([.tool_input.edits[]?.new_string] | join("\n")) + "\n" + (.tool_input.new_source // "")')"
  check_approval_fields "$(rel "$FILE")" "$NEW" ""; exit 0
fi
[ -z "$CMD" ] && exit 0
printf '%s' "$CMD" | grep -Eq "$APPROVE_PY_RE" && block "scripts/approve.py is run by a human from their own shell, never from an agent session."
printf '%s' "$CMD" | grep -Eq "$CLAUDECODE_RE" && block "unsetting CLAUDECODE is how an agent impersonates a human; not allowed."
[ "${BASH_WRITE_GUARD:-1}" = 1 ] || exit 0
WHERE=" (write detected in a Bash command)"
while IFS= read -r CAND; do
  [ -z "$CAND" ] && continue
  printf '%s' "$CAND" | grep -Eq "$ARTIFACT_RE" || continue
  check_approval_fields "$CAND" "$CMD" "$WHERE"
  printf '%s' "$CMD" | grep -Eiq 'approved|supersed' && block "'$CAND' is a chain artifact and the command mentions approval$WHERE. Use Write/Edit for drafts; approvals are a human act."
done < <(bash_write_candidates "$CMD" "work")
exit 0
