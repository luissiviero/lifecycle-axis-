#!/usr/bin/env bash
# Only a human approves. An agent may draft, revise and flip an artifact to in-review, but may
# never set `status: approved|superseded`, `approved-by:` or `approved-on:` on
# work/<slug>/{intent,spec,plan,incident}.md, nor run scripts/approve.py. The human unlock
# (SDLC_CONTROL_PLANE_UNLOCK) never applies here (work/approval-gate; knowledge/decisions/human-only-approvals.md).
#
# Two branches, like protect-paths.sh:
#   $FILE set   -> Edit/Write/MultiEdit/NotebookEdit: the edit is applied to a copy of the file's
#                  current text and the RESULTING front matter is compared with the current one, so
#                  a bare-value edit (`luissiviero` -> `mallory`) is judged by what it does, not by
#                  the words it uses (PR #25 review).
#   $FILE empty -> Bash: `approve.py` and any CLAUDECODE unset/reassignment are refused outright;
#                  then, when BASH_WRITE_GUARD is on, a write candidate that is a chain artifact
#                  already carrying an approval is refused (it changes only through Write/Edit, where
#                  the result can be checked), and a write to a draft is checked against the command
#                  text. The command text is a heuristic: an obfuscated command is the CI chain
#                  check's job (approval commit author, ledger), recorded as a residual.
. "$(dirname "$0")/_lib.sh"
ARTIFACT_RE='^work/[^/]+/(intent|spec|plan|incident)\.md$'
APPROVE_PY_RE='(^|[/[:space:]])approve\.py([[:space:]]|$)'
CLAUDECODE_RE='(env[[:space:]]+(-u|--unset)[[:space:]]+CLAUDECODE|unset[[:space:]]+CLAUDECODE|(^|[[:space:];&|])CLAUDECODE=)'

# compare_fields <repo-relative path> <new status> <new approved-by> <new approved-on> <where>
# Blocks when the new values are an approval-shaped change from the file's current front matter.
compare_fields() {
  local R="$1" ns="$2" nb="$3" no="$4" where="$5" cs cb co
  cs="$(fm_value "$ROOT/$R" status)"; cb="$(fm_value "$ROOT/$R" approved-by)"; co="$(fm_value "$ROOT/$R" approved-on)"
  case "$ns" in approved|superseded) [ "$ns" = "$cs" ] || block "'$R' would become status: $ns$where. Only a human approves: ask them to run scripts/approve.py from their own shell, then wait.";; esac
  [ -n "$nb" ] && [ "$nb" != "$cb" ] && block "'$R' would set approved-by: $nb$where. Only a human sets approved-by."
  [ -n "$no" ] && [ "$no" != "$co" ] && block "'$R' would set approved-on: $no$where. Only a human sets approved-on."
  return 0
}

# check_text <repo-relative path> <text> <where> -- Bash branch: judge by any key line in the text.
check_text() {
  local R="$1" text="$2" where="$3" ns nb no
  ns="$(printf '%s\n' "$text" | fm_value - status any)"
  nb="$(printf '%s\n' "$text" | fm_value - approved-by any)"
  no="$(printf '%s\n' "$text" | fm_value - approved-on any)"
  compare_fields "$R" "$ns" "$nb" "$no" "$where"
}

# check_result <repo-relative path> <resulting file text> -- edit branch: judge by the front matter
# of the file as it would be after the edit.
check_result() {
  local R="$1" result="$2" ns nb no
  ns="$(printf '%s\n' "$result" | fm_value - status)"
  nb="$(printf '%s\n' "$result" | fm_value - approved-by)"
  no="$(printf '%s\n' "$result" | fm_value - approved-on)"
  compare_fields "$R" "$ns" "$nb" "$no" ""
}

if [ -n "$FILE" ]; then
  R="$(rel "$FILE")"
  printf '%s' "$R" | grep -Eq "$ARTIFACT_RE" || exit 0
  # Write / NotebookEdit carry the whole new text; Edit / MultiEdit carry replacements to apply
  # to the current text (literal, first match unless replace_all; a missing old_string leaves the
  # text unchanged, as the tool itself would fail).
  RESULT="$(printf '%s' "$INPUT" | jq -r '.tool_input.content // .tool_input.new_source // empty')"
  if [ -z "$RESULT" ] && printf '%s' "$INPUT" | jq -e '.tool_input.new_string != null or .tool_input.edits != null' >/dev/null; then
    RESULT=""; [ -f "$ROOT/$R" ] && RESULT="$(cat "$ROOT/$R")"
    while IFS= read -r -d '' OLD && IFS= read -r -d '' NEW && IFS= read -r -d '' ALL; do
      [ -z "$OLD" ] && continue
      if [ "$ALL" = "true" ]; then RESULT="${RESULT//"$OLD"/"$NEW"}"; else RESULT="${RESULT/"$OLD"/"$NEW"}"; fi
    done < <(printf '%s' "$INPUT" | jq -j '.tool_input as $t | ($t.edits // [{old_string: $t.old_string, new_string: $t.new_string, replace_all: $t.replace_all}])[] | (.old_string // ""), "\u0000", (.new_string // ""), "\u0000", ((.replace_all // false) | tostring), "\u0000"')
  fi
  check_result "$R" "$RESULT"
  exit 0
fi

[ -z "$CMD" ] && exit 0
printf '%s' "$CMD" | grep -Eq "$APPROVE_PY_RE" && block "scripts/approve.py is run by a human from their own shell, never from an agent session."
printf '%s' "$CMD" | grep -Eq "$CLAUDECODE_RE" && block "unsetting CLAUDECODE is how an agent impersonates a human; not allowed."
[ "${BASH_WRITE_GUARD:-1}" = 1 ] || exit 0
WHERE=" (write detected in a Bash command)"
while IFS= read -r CAND; do
  [ -z "$CAND" ] && continue
  printf '%s' "$CAND" | grep -Eq "$ARTIFACT_RE" || continue
  CS="$(fm_value "$ROOT/$CAND" status)"; CB="$(fm_value "$ROOT/$CAND" approved-by)"
  case "$CS" in approved|superseded) block "'$CAND' is an approved chain artifact$WHERE; it changes only through Write/Edit, where the resulting front matter is checked. Approvals are a human act.";; esac
  [ -n "$CB" ] && block "'$CAND' carries approved-by: $CB$WHERE; it changes only through Write/Edit, where the resulting front matter is checked."
  check_text "$CAND" "$CMD" "$WHERE"
  printf '%s' "$CMD" | grep -Eiq 'approved|supersed' && block "'$CAND' is a chain artifact and the command mentions approval$WHERE. Use Write/Edit for drafts; approvals are a human act."
done < <(bash_write_candidates "$CMD" "work")
exit 0
