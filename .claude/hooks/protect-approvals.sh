#!/usr/bin/env bash
# Only a human approves. An agent may draft, revise and flip an artifact to in-review, but may
# never set `status: approved|superseded`, `approved-by:` or `approved-on:` on
# work/<slug>/{intent,spec,plan,incident}.md, nor run scripts/approve.py. The human unlock
# (SDLC_CONTROL_PLANE_UNLOCK) never applies here (work/approval-gate; knowledge/decisions/human-only-approvals.md).
#
# A second word, `delegated`, is an agent's own signature under a delegation grant the owner wrote
# on the item's intent (work/delegated-mode R-9, D5). It passes only when .sdlc/delegation.yaml is
# enabled, the artifact is signable there, it is not the intent that carries the grant, that intent
# says `mode: delegated`, and every approved-by in the result is an agent the policy lists. The
# grant keys themselves -- `mode`, `delegated-by`, `delegated-on` -- stay as human-only as
# approved-by, and a mutating `gh api` call on a contents/ or git/ path is refused outright: such a
# call would create a GitHub-signed commit in the owner's name (spec C3).
#
# Two branches, like protect-paths.sh:
#   $FILE set   -> Edit/Write/MultiEdit/NotebookEdit: the edit is applied to a copy of the file's
#                  current text and the RESULTING front matter is judged as a whole, so a bare-value
#                  edit (`luissiviero` -> `mallory`) is judged by what it does, not by the words it
#                  uses (PR #25 review).
#   $FILE empty -> Bash: `approve.py`, any CLAUDECODE unset/reassignment and a mutating `gh api`
#                  write are refused outright; then, when BASH_WRITE_GUARD is on, a write candidate
#                  that is a chain artifact already carrying an approval or a signature is refused
#                  (it changes only through Write/Edit, where the result can be checked), and a
#                  write to a draft is checked against the command text. The command text is a
#                  heuristic: an obfuscated command is the CI chain check's job (approval commit
#                  author, ledger), recorded as a residual.
. "$(dirname "$0")/_lib.sh"
ARTIFACT_RE='^work/[^/]+/(intent|spec|plan|incident)\.md$'
APPROVE_PY_RE='(^|[/[:space:]])approve\.py([[:space:]]|$)'
# GNU env also takes the glued `-uCLAUDECODE` and `--unset=CLAUDECODE` forms (PR #25 review).
CLAUDECODE_RE='(env[[:space:]]+(-u|--unset)[[:space:]=]*CLAUDECODE|unset[[:space:]]+CLAUDECODE|(^|[[:space:];&|])CLAUDECODE=)'
# A mutating `gh api` call on a contents/ or git/ path writes a commit through the API: GitHub signs
# it with its own key and attributes it to the token's owner, so a session holding a human login
# could forge a grant commit that looks like theirs (work/delegated-mode C3). A read-only `gh api`
# call is untouched; the mutation shape and the command boundary are production-gate.sh's.
GH_API_WRITE_RE='(^|[;&|(){}!]|[[:space:]])gh[[:space:]]+api[[:space:]]+[^;&|]*(contents/|git/)'
GH_MUT_RE='(-X|--method)[[:space:]=]*(POST|PUT|PATCH|DELETE)|(^|[[:space:]])(-f|-F|--field|--raw-field|--input)([[:space:]]|=)'
# The GraphQL route to the same commit: createCommitOnBranch, createRef and updateRef write file
# contents or move a ref through `gh api graphql`, server-signed and attributed to the token's owner
# exactly as the REST call is (PR #43 security pass, finding 3). A read-only GraphQL query is untouched.
GH_GRAPHQL_WRITE_RE='(^|[;&|(){}!]|[[:space:]])gh[[:space:]]+api[[:space:]]+[^;&|]*(createCommitOnBranch|createRef|updateRef)'

# compare_fields <repo-relative path> <new status> <new approved-by> <new approved-on> <where>
# Blocks when the new values are an approval-shaped change from the file's current front matter.
compare_fields() {
  local R="$1" ns="$2" nb="$3" no="$4" where="$5" cs cb co
  cs="$(fm_value "$ROOT/$R" status)"; cb="$(fm_value "$ROOT/$R" approved-by)"; co="$(fm_value "$ROOT/$R" approved-on)"
  case "$ns" in approved|superseded) [ "$ns" = "$cs" ] || block "'$R' would become status: $ns$where. Only a human approves: ask them to run scripts/approve.py from their own shell, then wait.";;
    # A signature is written by scripts/sign.py, never by a Bash write to the artifact (PR #43 security pass, nit 1).
    delegated) [ "$ns" = "$cs" ] || block "'$R' would become status: delegated$where. A signature is written by scripts/sign.py under the session's own agent handle, never by a Bash write.";; esac
  [ -n "$nb" ] && [ "$nb" != "$cb" ] && block "'$R' would set approved-by: $nb$where. Only a human sets approved-by."
  [ -n "$no" ] && [ "$no" != "$co" ] && block "'$R' would set approved-on: $no$where. Only a human sets approved-on."
  return 0
}

# check_text <repo-relative path> <text> <where> -- Bash branch: judge by any key line in the text.
# `mode` is read here too, by the same rule as the edit branch: the grant is the owner's own act,
# whichever tool would write it (work/delegated-mode R-9).
check_text() {
  local R="$1" text="$2" where="$3" ns nb no nm cm
  ns="$(printf '%s\n' "$text" | fm_value - status any)"
  nb="$(printf '%s\n' "$text" | fm_value - approved-by any)"
  no="$(printf '%s\n' "$text" | fm_value - approved-on any)"
  nm="$(printf '%s\n' "$text" | fm_value - mode any)"
  cm="$(fm_value "$ROOT/$R" mode)"; cm="${cm:-supervised}"
  [ -n "$nm" ] && [ "$nm" != "$cm" ] && block "'$R' would set mode: $nm$where. Only a human sets mode, delegated-by and delegated-on: the delegation grant is the owner's own commit."
  compare_fields "$R" "$ns" "$nb" "$no" "$where"
}

# fm_all <text> <key> -- every value of <key> in the first front-matter block, one per line, cleaned
# like fm_value. A duplicated key is a decoy (PR #25 review): the hook judges every occurrence,
# whichever one a later reader would pick.
fm_all() {
  printf '%s\n' "$1" | awk -v k="$2" '
    { sub(/\r$/, "") }
    /^---[[:space:]]*$/ { c++; if (c == 2) exit; next }
    c == 1 && index($0, k ":") == 1 {
      v = substr($0, length(k) + 2)
      sub(/^[[:space:]]+/, "", v); sub(/[[:space:]]+#.*$/, "", v); if (v ~ /^#/) v = ""
      sub(/[[:space:]]+$/, "", v)
      if (length(v) >= 2 && substr(v, 1, 1) == substr(v, length(v), 1) && (substr(v, 1, 1) == "\"" || substr(v, 1, 1) == "\047")) v = substr(v, 2, length(v) - 2)
      print tolower(v) }'
}

# check_result <repo-relative path> <resulting file text> -- edit branch: judge the front matter of
# the file as it would be after the edit, every occurrence of every key, as one decision (R-9, D5).
# In order: the human-only words; the grant keys, which no agent writes; a signature, which carries
# its own approved-by and is checked by check_signature; otherwise the approval fields, as before.
check_result() {
  local R="$1" result="$2" v cs cm cb co name slug signature=0
  cs="$(fm_value "$ROOT/$R" status)"
  cm="$(fm_value "$ROOT/$R" mode)"; cm="${cm:-supervised}"   # no key, or no file yet, means supervised
  cb="$(fm_value "$ROOT/$R" delegated-by)"; co="$(fm_value "$ROOT/$R" delegated-on)"
  name="${R##*/}"; slug="${R#work/}"; slug="${slug%%/*}"     # ARTIFACT_RE: work/<slug>/<name>
  while IFS= read -r v; do
    case "$v" in approved|superseded) compare_fields "$R" "$v" "" "" "";; esac
    [ "$v" = delegated ] && [ "$v" != "$cs" ] && signature=1
  done < <(fm_all "$result" status)
  while IFS= read -r v; do
    [ -n "$v" ] && [ "$v" != "$cm" ] && block "'$R' would set mode: $v. Only a human sets mode, delegated-by and delegated-on: the delegation grant is the owner's own commit (scripts/approve.py --delegate, or the web editor)."
  done < <(fm_all "$result" mode)
  while IFS= read -r v; do
    [ -n "$v" ] && [ "$v" != "$cb" ] && block "'$R' would set delegated-by: $v. Only a human sets mode, delegated-by and delegated-on."
  done < <(fm_all "$result" delegated-by)
  while IFS= read -r v; do
    [ -n "$v" ] && [ "$v" != "$co" ] && block "'$R' would set delegated-on: $v. Only a human sets mode, delegated-by and delegated-on."
  done < <(fm_all "$result" delegated-on)
  if [ "$signature" = 1 ]; then check_signature "$R" "$name" "$slug" "$result" "$cs"; return 0; fi
  while IFS= read -r v; do compare_fields "$R" "" "$v" "" ""; done < <(fm_all "$result" approved-by)
  while IFS= read -r v; do compare_fields "$R" "" "" "$v" ""; done < <(fm_all "$result" approved-on)
  return 0
}

# check_signature <path> <artifact name> <slug> <resulting text> -- the result would become
# `status: delegated`, which is an agent signing under the owner's grant (R-9). Every condition is
# the policy's or the owner's, never the session's; the first one that fails is the message. When
# they all hold, the signature's own approved-by and approved-on may change, which is the one case
# where they may.
check_signature() {
  local R="$1" name="$2" slug="$3" result="$4" current="$5" v mode signer=0 policy=".sdlc/delegation.yaml"
  # A human's approval is never overwritten by an Edit: re-deciding it is sign.py --revision's job,
  # with the consensus record that script checks (PR #43 security pass, finding 2).
  [ "$current" = approved ] && block "'$R' is approved by a human; only a human, or scripts/sign.py --revision with a consensus record, re-decides it. An Edit never replaces an approval with a signature."
  delegation_on || block "'$R' would become status: delegated, but delegated mode is off ($policy is missing or does not say enabled: true). Only a human approves: ask them to run scripts/approve.py from their own shell, then wait."
  artifact_signable "$name" || block "'$R' would become status: delegated, but '$name' is not in the signable list of $policy. Only a human approves it."
  [ "$name" = intent.md ] && block "'$R' would become status: delegated, but the intent carries the delegation grant and is never signed by an agent. Only a human approves it."
  mode="$(intent_mode "$slug")"
  [ "$mode" = delegated ] || block "'$R' would become status: delegated, but work/$slug/intent.md says mode: $mode. The grant is the owner's own commit; ask for it, then wait."
  while IFS= read -r v; do
    [ -n "$v" ] || continue
    signer=1
    agent_handle_ok "$v" || block "'$R' would become status: delegated with approved-by: $v, who is not an agent listed in $policy. A signature is written by scripts/sign.py under the session's own agent handle."
  done < <(fm_all "$result" approved-by)
  [ "$signer" = 1 ] || block "'$R' would become status: delegated with no approved-by. A signature names the agent that made it; scripts/sign.py writes the status, the handle and the ledger line together."
  return 0
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
printf '%s' "$CMD" | grep -Eq "$GH_GRAPHQL_WRITE_RE" && block "that command writes a commit or a ref through the GitHub GraphQL API: the API would create a GitHub-signed commit; a grant is the owner's own act. Push a branch and open a pull request instead."
printf '%s' "$CMD" | grep -Eiq "$GH_API_WRITE_RE" && printf '%s' "$CMD" | grep -Eiq "$GH_MUT_RE" && block "that command writes through the GitHub contents/ or git/ API: the API would create a GitHub-signed commit; a grant is the owner's own act. Push a branch and open a pull request instead."
[ "${BASH_WRITE_GUARD:-1}" = 1 ] || exit 0
WHERE=" (write detected in a Bash command)"
# A `mode:` line anywhere in the command is what turns the word rule on for `delegat` below; the
# value itself is judged against the target's current mode by check_text.
TEXT_MODE="$(printf '%s\n' "$CMD" | fm_value - mode any)"
while IFS= read -r CAND; do
  [ -z "$CAND" ] && continue
  printf '%s' "$CAND" | grep -Eq "$ARTIFACT_RE" || continue
  CS="$(fm_value "$ROOT/$CAND" status)"; CB="$(fm_value "$ROOT/$CAND" approved-by)"
  case "$CS" in
    approved|superseded) block "'$CAND' is an approved chain artifact$WHERE; it changes only through Write/Edit, where the resulting front matter is checked. Approvals are a human act.";;
    delegated) block "'$CAND' is a signed chain artifact$WHERE; it changes only through Write/Edit, where the resulting front matter is checked. A signature is written by scripts/sign.py.";;
  esac
  [ -n "$CB" ] && block "'$CAND' carries approved-by: $CB$WHERE; it changes only through Write/Edit, where the resulting front matter is checked."
  check_text "$CAND" "$CMD" "$WHERE"
  # A `status: delegated` anywhere in the text (a printf, not only a heredoc line) is a signature by
  # Bash, which the honest path never needs (PR #43 security pass, nit 1).
  printf '%s' "$CMD" | grep -Eiq 'status:[[:space:]]*delegated' && block "'$CAND' would be given status: delegated$WHERE. A signature is written by scripts/sign.py under the session's own agent handle, never by a Bash write."
  # `delegat` joins the word rule only where a delegation word would be an act: the intent that
  # carries the grant, or a command that writes a `mode:` line. Elsewhere the word is prose, and a
  # legitimate `python3 scripts/sign.py ...` names no write candidate at all, so it never gets here.
  WORD_RE='approved|supersed'
  { [ "${CAND##*/}" = intent.md ] || [ -n "$TEXT_MODE" ]; } && WORD_RE="$WORD_RE|delegat"
  printf '%s' "$CMD" | grep -Eiq "$WORD_RE" && block "'$CAND' is a chain artifact and the command mentions approval$WHERE. Use Write/Edit for drafts; approvals are a human act."
done < <(bash_write_candidates "$CMD" "work")
exit 0
