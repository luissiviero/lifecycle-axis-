---
type: sdlc/spec
id: approval-gate
title: Only a human can flip an artifact to approved
description: A PreToolUse hook that refuses agent writes to the approval fields of chain artifacts and agent invocations of approve.py, plus an approver check in require-plan.sh.
stage: design
status: approved
reads: intent.md
approved-by: luissiviero
approved-on: 2026-09-05
skills-applied: [security-standards]
skills-version: 60ab0f5
prompt: "Transcribed from the approved implementation plan (session above), section WI-6 and appendix A1, by a drafting subagent; reviewed by the orchestrator."
record:
resource: https://claude.ai/code/session_01DSYmeD7eng2GKQ3EbHQDzo
tags: [hooks, approvals, chain-check, approve, consensus-item-1]
timestamp: 2026-09-04T21:49:27Z
---
# Spec: only a human can flip an artifact to approved

## Requirements (each maps to an intent outcome)
| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R-1 | Edit/Write/MultiEdit/NotebookEdit to `work/<slug>/{intent,spec,plan,incident}.md` whose new text sets `status: approved` or `superseded`, or a non-empty `approved-by:`/`approved-on:` differing from the file's current value, exits 2 | outcome 1 | `scripts/test_protect_approvals.py::EditBranch` block cases 1 to 4 |
| R-2 | The same tools pass for `status: in-review`, a verbatim template copy, an approved artifact whose new text repeats its current values, and any file outside the artifact pattern | outcome 1 | `scripts/test_protect_approvals.py::EditBranch` allow cases 1 to 4 |
| R-3 | Bash commands invoking `approve.py`, or unsetting/reassigning `CLAUDECODE`, exit 2 regardless of `BASH_WRITE_GUARD` | outcome 2 | `scripts/test_protect_approvals.py::BashBranch` block cases 5 and 6 |
| R-4 | Bash commands whose write candidates include a chain artifact and whose text sets an approval field or mentions `approved`/`supersed` exit 2; read-only commands pass | outcome 2 | `scripts/test_protect_approvals.py::BashBranch` block cases 7, 8; allow case 5 |
| R-5 | `SDLC_CONTROL_PLANE_UNLOCK=1` does not change any verdict of the new hook | outcome 2 | `scripts/test_protect_approvals.py::EditBranch::test_unlock_set_still_blocks` |
| R-6 | `require-plan.sh` blocks when the approved plan's `approved-by` is empty, is `claude`, is not in the plan's role, or the approvers file is missing; `"@LuisSiviero"` passes | outcome 3 | `scripts/test_hooks_baseline.py::RequirePlanHook` four new cases |
| R-7 | The hook is registered after `protect-tests.sh` on both matchers in `.claude/settings.json`, in `docs/sdlc/templates/claude-settings.json`, and in `.gemini/settings.json` | outcome 4 | `python3 scripts/run_tests.py -p test_gemini_wiring.py` ends `OK`; `python3 scripts/run_tests.py -p test_adopt.py` ends `OK` |
| R-8 | An eval case pins the gate | outcome 5 | `scripts/run_evals.sh --only hook-blocks-agent-approval` ends `EVALS: 1 pass, 0 fail, ...` |
| R-9 | Whole suite green | outcome 5 | `scripts/verify.sh` ends `VERIFY: PASS (<sha>)` |

## Design
### Architecture / data flow
One new PreToolUse hook, `.claude/hooks/protect-approvals.sh`, sourced from `_lib.sh` like the others
and registered last on the edit matcher and after `protect-tests.sh` on the Bash matcher. Edit branch:
it reads the new text from the tool input, extracts `status`, `approved-by`, `approved-on` from it,
reads the same keys from the file on disk, and blocks on an approval-shaped change. Bash branch: two
regex rules run first (`approve.py`, `CLAUDECODE`), then, when `BASH_WRITE_GUARD` is on, every write
candidate from `bash_write_candidates` that matches the artifact pattern is checked against the whole
command text. The human unlock is never consulted. `require-plan.sh` gains one line pair after its
status check that validates `approved-by` against the plan's role. Appendix A1, verbatim as approved
(the shipped hook diverges after the PR #25 review, as recorded in `plan.md`'s deviations log and in
`knowledge/decisions/human-only-approvals.md`: the edit branch applies the edit to the current text and
judges every approval key of the resulting front matter; the Bash branch refuses any write candidate that
is an already-approved artifact; the `env` unset rule also matches the glued `-uCLAUDECODE` form):

```bash
#!/usr/bin/env bash
# Only a human approves. An agent may draft, revise and flip an artifact to in-review, but may
# never set `status: approved|superseded`, `approved-by:` or `approved-on:` on
# work/<slug>/{intent,spec,plan,incident}.md, nor run scripts/approve.py. The human unlock
# (SDLC_CONTROL_PLANE_UNLOCK) never applies here.
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
```

### Interfaces (APIs, events, schemas) — exact shapes
Helpers this hook calls, added to `_lib.sh` by `control-plane-visibility` (appendix A1, verbatim):

```bash
fm_value() {  # <file|-> <key> [any]  -> value with CR, trailing ` # comment`, quotes stripped; casefolded
  awk -v k="$2" -v any="${3:-}" '
    { sub(/\r$/, "") }
    !any && /^---[[:space:]]*$/ { c++; if (c == 2) exit; next }
    (any || c == 1) && index($0, k ":") == 1 {
      v = substr($0, length(k) + 2)
      sub(/^[[:space:]]+/, "", v); sub(/[[:space:]]+#.*$/, "", v); if (v ~ /^#/) v = ""
      sub(/[[:space:]]+$/, "", v)
      if (length(v) >= 2 && substr(v, 1, 1) == substr(v, length(v), 1) && (substr(v, 1, 1) == "\"" || substr(v, 1, 1) == "\047")) v = substr(v, 2, length(v) - 2)
      print tolower(v); exit }' "$1" 2>/dev/null
}
artifact_role() {  # <artifact> -> role under `artifacts:` in APPROVERS_FILE
  awk -v a="$1" '{ sub(/\r$/, "") } /^[A-Za-z]/ { top = $0; sub(/:.*/, "", top) }
    top == "artifacts" && index($0, "  " a ":") == 1 { v = $0; sub(/^[^:]*:[[:space:]]*/, "", v); sub(/[[:space:]]*#.*$/, "", v); print v; exit }' \
    "$ROOT/${APPROVERS_FILE:-.sdlc/approvers.yaml}" 2>/dev/null
}
approver_has_role() {  # <handle> <role> -> 0 when listed under roles.<role> and not in never-approve; missing file fails closed
  local f="$ROOT/${APPROVERS_FILE:-.sdlc/approvers.yaml}" h="$1"
  h="${h//\"/}"; h="${h//\'/}"; h="${h#"${h%%[![:space:]]*}"}"; h="${h%%[[:space:]]*}"; h="${h#@}"; h="${h,,}"
  [ -n "$h" ] && [ -f "$f" ] || return 1
  awk -v role="$2" -v h="$h" '
    function norm(x) { gsub(/^[[:space:]]+|[[:space:]]+$/, "", x); gsub(/^["\047]|["\047]$/, "", x); sub(/^@/, "", x); return tolower(x) }
    function has(list,   n, a, i) { sub(/^[[:space:]]*\[/, "", list); sub(/\][[:space:]]*(#.*)?$/, "", list)
      n = split(list, a, ","); for (i = 1; i <= n; i++) if (norm(a[i]) == h) return 1; return 0 }
    { sub(/\r$/, "") }
    /^[A-Za-z]/ { top = $0; sub(/:.*/, "", top) }
    /^never-approve:/ { v = $0; sub(/^never-approve:/, "", v); if (has(v)) bad = 1 }
    top == "roles" && index($0, "  " role ":") == 1 { v = $0; sub(/^[^:]*:/, "", v); if (has(v)) ok = 1 }
    END { exit (ok && !bad) ? 0 : 1 }' "$f"
}
```

`require-plan.sh`, inserted after line 20 (the `[ "$STATUS" = "approved" ] || block ...` line):

```bash
  BY="$(fm_value "$PLAN" approved-by)"; ROLE="$(artifact_role plan.md)"; ROLE="${ROLE:-tech-lead}"
  approver_has_role "$BY" "$ROLE" || block "'$R' needs an approved plan$where: work/$SLUG/plan.md says approved-by '$BY', who is not a $ROLE in ${APPROVERS_FILE:-.sdlc/approvers.yaml} (or the file is missing). A listed human must approve with scripts/approve.py."
```

Wiring: `.claude/settings.json` gains `{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-approvals.sh" }` after line 13 and after line 22 (both `protect-tests.sh` entries); `docs/sdlc/templates/claude-settings.json` the same after lines 10 and 19; `.gemini/settings.json` gains `{ "name": "sdlc-protect-approvals", "type": "command", "command": "bash .claude/hooks/protect-approvals.sh" }` after line 11 (its `sdlc-protect-tests` entry, on the `write_file|replace|run_shell_command` matcher).

Test cases for `scripts/test_protect_approvals.py` (appendix A1, verbatim). Block (rc 2): Edit `new_string` `status: approved`; Edit `approved-by: luissiviero`; Write of a template-shaped file with `status: superseded`; MultiEdit whose second edit sets `approved-on: 2026-09-04`; Bash `python3 scripts/approve.py foo intent.md --as luissiviero`; Bash `env -u CLAUDECODE python3 scripts/approve.py foo plan.md`; Bash `sed -i 's/draft/approved/' work/foo/intent.md`; Bash heredoc writing `status: approved` into `work/foo/plan.md`. Allow (rc 0): Edit `status: in-review`; Write of a draft intent copied verbatim from the template; Edit on an already-approved plan whose `new_string` repeats the unchanged values; Edit to `docs/x.md` containing `status: approved`; Bash `cat work/foo/plan.md`; unlock set + Edit to `approved` still rc 2. Fixture: `work/foo/intent.md` with `status: draft`; the approved-plan case adds `work/foo/plan.md` with `status: approved`, `approved-by: luissiviero`, `approved-on: 2026-09-04`. `RequirePlanHook` new cases: `approved-by: claude` blocks; `approved-by: someone-else` blocks; approvers file missing blocks; `approved-by: "@LuisSiviero"` allows.

### Data and migrations
None. No new fields; `.sdlc/approvers.yaml` is read, never written. No personal or regulated data.

### Failure modes and how they surface
- No `jq`: `_lib.sh:42-46` already blocks with the install hint.
- `_lib.sh` helpers absent (item landed out of order): `fm_value: command not found` on stderr; the
  plan's step 1 preflight checks for them from a second shell before anything is wired.
- Approvers file missing or unreadable: `approver_has_role` returns 1; `require-plan.sh` blocks and
  names the file. False positive on the Bash branch: one stderr line; the agent retries with Write.
- Wrong hook registration: `test_gemini_wiring.py` and `test_control_plane_hardening.py` fail before
  a session ever runs it; a session that already started keeps the old wiring until restart.

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: the hook reads the current file to decide whether a value "changed", so an agent that first demotes an approved artifact to `in-review` and then re-approves it is blocked only on the second step; the demotion itself passes — policy: security-standards §8 — contradiction? no — owner: luissiviero — resolution: accepted; demotion loses an approval and the chain check reports it; intent open question 1.
- C2: the `approved|supersed` word rule on the Bash branch blocks a heredoc that merely quotes the word in prose while writing a chain artifact — policy: CLAUDE.md rule 1 spirit (fail closed) — contradiction? no — owner: luissiviero — resolution: accepted; drafts go through Write/Edit; intent open question 2.
- C3: an eval or test that intentionally runs `approve.py` under `CLAUDECODE=1` (`evals/cases/approve-refuses-in-agent-session.yaml:5`) would be blocked if an agent ran that check line by hand through Bash — policy: security-standards §8 — contradiction? no — owner: luissiviero — resolution: `scripts/run_evals.sh` executes the check itself, so the normal path is unaffected; documented in the decision record.
- C4: `require-plan.sh` now fails closed on a fake repo without `.sdlc/approvers.yaml`, so every test whose plan says `status: approved` depends on the `front-matter` item's `hooktest.fake_repo` copying the file — policy: rule 1 — contradiction? no — owner: luissiviero — resolution: landing order (front-matter, then control-plane-visibility, then this).

## Open questions carried from intent.md
- Q1 (block demotions?) and Q2 (narrow the word rule?) stay open; the design assumes the proposed answers (no; keep broad).

## Decisions (ADR-style: context → decision → consequences)
- D1: the hook compares new values with the file's current values rather than blocking every write that mentions an approval field → an approved plan's deviations log stays editable → the demotion path in C1 is accepted.
- D2: awk helpers in `_lib.sh`, not a `python3` call → about 2 ms per hook and no dependency on the Windows Store stub → `fm_value` casefolds, so values are compared lowercase.
- D3: the unlock is not consulted anywhere in the new hook → the kit repo's own sessions cannot approve either → the owner approves from their shell, as the plan already requires.
- D4: `approve.py` and `CLAUDECODE` rules run before the `BASH_WRITE_GUARD` switch → an adopter who turns the write guard off keeps the two cheap rules.

## Gotchas found while reading the codebase
- `.gemini/settings.json:11` is the `sdlc-protect-tests` entry; the plan says "after line 10", which would put the new hook before `protect-tests`. Insert after line 11 to keep the same order as the Claude matcher.
- `scripts/check_plugin_manifest.py:255-287` inspects only a `hooks` field inside `.claude-plugin/plugin.json`, and that file (`:1-23`) has none; nothing enumerates the hooks directory, so the plan's "if needed" edit is not needed and the file leaves the list.
- `scripts/test_gemini_wiring.py:61-71` requires every wired hook to exist and be executable, so the new file must be committed with mode 100755 (an earlier connector push dropped exec bits); `:80-81` names four required hooks per tool, and adding the fifth pins the wiring.
- `approver_has_role` uses `${h,,}` (bash 4); the awk `norm()` lowercases again, so the shell step is redundant and would fail on bash 3.2 (stock macOS). Not a target platform today; noted for the deviations log if it bites.
- `fm_value ... any` matches a line starting at column 1 with `status:`; a body line written that way inside an artifact (a fenced example, say) trips the block. Indent such examples.
- `hook-requires-approved-plan.yaml:10` and `test_gemini_wiring.py:141-148` use a work item that does not exist, so `require-plan.sh` blocks before the new approver line; unaffected. `run_evals.sh:51` already unsets the unlock for hook oracles.

## Not doing
- Blocking a demotion from `approved` to `in-review` (C1); validating `approved-on` as a date (the chain check's job).
- Changing `check_artifact_chain.py`'s author check; it stays the CI backstop for web-editor approvals.
- Touching `production-gate.sh` or `.sdlc/release-authorizations` (the `deploy-gate` item).
