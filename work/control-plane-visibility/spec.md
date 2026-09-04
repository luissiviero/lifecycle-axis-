---
type: sdlc/spec
id: control-plane-visibility
title: Hook decisions must be logged; the control-plane unlock must be visible; CI must recognise the kit's own agent PRs
description: A tab-separated decision log written by every hook, a systemMessage on every unlocked write, three never-unlock paths, and agent detection by branch prefix list or commit trailer in check_control_plane.sh.
stage: design
status: in-review
reads: intent.md
approved-by:
approved-on:
skills-applied: [security-standards]
skills-version: 60ab0f5
prompt: "Transcribed from the approved implementation plan (session above), section WI-2 and appendix A2 (plus the never-unlock list in A5 and the helper shapes in A1), by a drafting subagent; reviewed by the orchestrator."
record:
resource: https://claude.ai/code/session_01DSYmeD7eng2GKQ3EbHQDzo
tags: [hooks, control-plane, unlock, audit-log, ci, consensus-item-2, consensus-item-4]
timestamp: 2026-09-04T21:46:58Z
---
# Spec: hook decisions must be logged; the control-plane unlock must be visible; CI must recognise the kit's own agent PRs

## Requirements (each maps to an intent outcome)
Intent outcomes: (1) every block, ask and unlock decision is logged durably; (2) an unlocked write is visible to
the user; (3) three human-only paths are never unlocked; (4) CI recognises the kit's own agent PRs; (5) `_lib.sh`
gains the additive helpers and input fields later items need; (6) docs match the code and the suite stays green.

| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R-1 | `log_decision <verdict> <detail>` in `_lib.sh` appends one line of six tab-separated fields (UTC RFC3339, verdict, hook basename, tool, session id, detail) to `$ROOT/.sdlc/hook-decisions.log`; `block()` and `ask()` call it before exiting | 1 | `scripts/test_lib_helpers.py::test_log_decision_appends_six_tab_fields`; `scripts/test_bash_plan_gates.py::DecisionLog::test_block_is_logged`, `::test_ask_is_logged` |
| R-2 | A failed log write (missing or read-only `.sdlc/`) never changes a verdict or the hook's exit code | 1 | `scripts/test_bash_plan_gates.py::DecisionLog::test_read_only_sdlc_does_not_break_hook` (skipped on Windows); `scripts/test_lib_helpers.py::test_log_decision_failure_is_silent` |
| R-3 | The unlock branch of `protect-paths.sh` keeps its stderr line byte-identical, logs `unlock`, and on exit 0 emits exactly one `{"systemMessage": ...}` naming every unlocked path; no output at all when nothing was unlocked | 2 | `scripts/test_bash_plan_gates.py::UnlockOnEditBranch::test_unlock_appends_log_line`, `::test_unlock_emits_one_system_message_for_two_targets`, existing `::test_unlock_leaves_unprotected_paths_silent`; eval `evals/cases/hook-unlock-writes-decision-log.yaml` |
| R-4 | No hook ever emits `permissionDecision: allow` | 2 | `scripts/test_bash_plan_gates.py::UnlockOnEditBranch::test_unlock_never_emits_permission_decision`; `grep -rn 'permissionDecision:"allow"' .claude/hooks` prints nothing |
| R-5 | With the unlock set, a write to `.sdlc/release-authorizations`, anything under it, `.sdlc/approvers.yaml` or `.sdlc/hook-decisions.log` is blocked (exit 2) on both branches | 3 | `scripts/test_bash_plan_gates.py::NeverUnlock::test_release_authorizations_blocked_under_unlock`, `::test_approvers_yaml_blocked_under_unlock`, `::test_decision_log_blocked_under_unlock`, `::test_bash_redirect_into_release_authorizations_blocked_under_unlock` |
| R-6 | `check_control_plane.sh` reads `AGENT_BRANCH_PREFIXES` from `.sdlc/config.env` (new key, default `claude/ kit/ spike/`); a `kit/foo` head ref without the label is BLOCKED; `work/x` stays human | 4 | `scripts/test_check_control_plane.py::test_kit_branch_no_label_is_blocked`, `::test_prefixes_come_from_config_env`; existing `::test_human_on_work_branch_touching_protected_path_passes` |
| R-7 | A commit in `base..HEAD` whose body matches `^(Co-Authored-By:.*Claude|Claude-Session:)` (case-insensitive) makes the PR agent-authored; a trailer only on a base commit does not; trailer plus label is EXEMPT | 4 | `scripts/test_check_control_plane.py::test_claude_coauthor_trailer_on_work_branch_is_blocked`, `::test_claude_session_trailer_is_blocked`, `::test_trailer_with_label_is_exempt`, `::test_trailer_only_on_base_commit_is_human`; eval `evals/cases/ci-control-plane-detects-agent-trailer.yaml` |
| R-8 | `_lib.sh` reads `CWD` and `SESSION_ID` from the input; `FILE` falls back to `.tool_input.notebook_path`; `rel()` resolves a relative path against `CWD` when set; `fm_value`, `artifact_role`, `approver_has_role` exist with the A1 shapes | 5 | `scripts/test_lib_helpers.py::test_cwd_and_session_id_read_from_input`, `::test_file_falls_back_to_notebook_path`, `::test_rel_resolves_relative_path_against_cwd`, `::test_fm_value_strips_cr_comment_and_quotes`, `::test_fm_value_any_reads_past_front_matter`, `::test_artifact_role_reads_approvers_file`, `::test_approver_has_role_accepts_listed_handle`, `::test_approver_has_role_rejects_never_approve`, `::test_approver_has_role_missing_file_fails_closed` |
| R-9 | Every existing hook verdict is unchanged; `.gitignore` lists `.sdlc/hook-decisions.log` and `monitoring/series/`; the docs named in the plan say what the code does | 6 | `python3 scripts/run_tests.py` ends `OK`; `scripts/verify.sh` ends `VERIFY: PASS (<sha>)`; `scripts/run_evals.sh` ends `0 fail`; `git check-ignore .sdlc/hook-decisions.log monitoring/series/x` prints both |

## Design
### Architecture / data flow
Every hook sources `_lib.sh` (`protect-paths.sh:19`, `require-plan.sh:22` and so on). Today `_lib.sh:48-50` reads
`TOOL`, `FILE`, `CMD` from the JSON on stdin and `:79-80` define `block()` and `ask()`. The change adds, after
line 50, `CWD` and `SESSION_ID` from the same input, and after line 78 a `DECISION_LOG` path plus `log_decision`,
which `block()` and `ask()` call first. The log is an append-only TSV under `.sdlc/`, git-ignored, one line per
decision, written by the hook process (not by an agent tool call). `protect-paths.sh` keeps its `check_target`
(`:21-33`); the unlock branch at `:24-25` additionally logs `unlock` and records the path in an `UNLOCKED`
array; both `exit 0` paths (`:37`, `:48`) go through `finish()`, which prints one `systemMessage` JSON when the
array is non-empty. A never-unlock `case` runs before the `PROTECTED_PATHS` test at `:23`.
`scripts/check_control_plane.sh` keeps its structure; `:35` reads `AGENT_BRANCH_PREFIXES` from the sourced
config with a wider default, and the `agent_authored` test at `:76-79` gains a third disjunct that scans commit
bodies in `base..HEAD`. `sdlc-gate.yml` is untouched: `:19` already fetches full history and `:37-44` already
passes author type, head ref and labels.

### Interfaces (APIs, events, schemas) — exact shapes
`_lib.sh` after line 50 (A2):
```bash
{ IFS= read -r CWD; IFS= read -r SESSION_ID; } < <(printf '%s' "$INPUT" | jq -r '(.cwd // ""), (.session_id // "")')
CWD="${CWD//\\//}"
```
`_lib.sh` after line 78 (A2):
```bash
DECISION_LOG="$ROOT/.sdlc/hook-decisions.log"
log_decision() {  # <verdict> <detail>; never fails the hook
  { printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" "$(basename "$0")" "${TOOL:-?}" "${SESSION_ID:-?}" "$2" >> "$DECISION_LOG"; } 2>/dev/null || true
}
block() { log_decision block "$1"; printf 'SDLC hook blocked this action: %s\n' "$1" >&2; exit 2; }
ask()   { log_decision ask "$1"; jq -n --arg r "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"ask",permissionDecisionReason:$r}}'; exit 0; }
```
`protect-paths.sh` (A2): `UNLOCKED=()`; the unlock branch keeps its stderr line and adds
`log_decision unlock "$R$where"; UNLOCKED+=("$R")`; both exit-0 paths call:
```bash
finish() {
  [ "${#UNLOCKED[@]}" -gt 0 ] || exit 0
  jq -n --arg m "SDLC: control-plane unlock used: wrote ${UNLOCKED[*]} (logged in .sdlc/hook-decisions.log)" '{systemMessage:$m}'
  exit 0
}
```
`protect-paths.sh` `check_target`, before the `PROTECTED_PATHS` test (A5):
```bash
  case "$R" in
    .sdlc/release-authorizations|.sdlc/release-authorizations/*|.sdlc/approvers.yaml|.sdlc/hook-decisions.log)
      block "'$R' is a human-only file$where. The control-plane unlock never covers it; the release manager / repo owner writes it from their own shell.";;
  esac
```
`check_control_plane.sh` lines 35 and 76-79 (A2):
```bash
: "${AGENT_BRANCH_PREFIXES:=claude/ kit/ spike/}"   # also a key in .sdlc/config.env (config wins)
AGENT_TRAILER_RE='^(Co-Authored-By:.*Claude|Claude-Session:)'
has_agent_trailer() { git -C "$ROOT" log --format=%B "${BASE}..HEAD" 2>/dev/null | grep -Eiq "$AGENT_TRAILER_RE"; }
agent_authored=0
if [ "$SDLC_PR_AUTHOR_TYPE" = "Bot" ] || is_agent_branch "$SDLC_PR_HEAD_REF" || has_agent_trailer; then agent_authored=1; fi
```
`.sdlc/config.env` gains, next to `CONTROL_PLANE_LABEL` (`:40-41`), a commented key
`AGENT_BRANCH_PREFIXES="claude/ kit/ spike/"`. `.gitignore` gains `.sdlc/hook-decisions.log` and
`monitoring/series/`. The helpers `fm_value <file|-> <key> [any]`, `artifact_role <artifact>` and
`approver_has_role <handle> <role>` are the awk functions quoted in appendix A1, copied verbatim; nothing in
this item calls them yet. `FILE` at `_lib.sh:49` becomes `.tool_input.file_path // .tool_input.notebook_path // empty`;
`rel()` at `:75` becomes `canon "$1" "${CWD:-}"` (an absolute path is unaffected by the second argument, `canon:57-58`).
Log line example (tabs shown as `<TAB>`):
`2026-09-04T21:50:00Z<TAB>unlock<TAB>protect-paths.sh<TAB>Edit<TAB>abc123<TAB>.sdlc/config.env`.
`scripts/test_lib_helpers.py` (new) drives each helper through
`bash -c '. "$1/_lib.sh"; <call>' _ <hooks dir> ...` with `input="{}"` or a crafted JSON, the pattern of
`scripts/test_gemini_wiring.py:116-121` (`_canon`), with `CLAUDE_PROJECT_DIR` pointing at a `fake_repo`.

### Data and migrations
No schema, no personal or regulated data. The log holds a timestamp, a verdict word, a hook name, a tool
name, the Claude Code session id (an opaque correlation id) and the reason text the hook already prints; it
is classified internal, git-ignored, and lives only on the machine that ran the hook. No migration: a missing
log file is created on first append.

### Failure modes and how they surface
- `.sdlc/` missing or read-only: `log_decision` swallows the error (`2>/dev/null || true`); the verdict is
  unchanged; nothing is logged. Surfaces only as an absent line; R-2 pins the behaviour.
- `jq` missing: `_lib.sh:42-47` already fails closed before any of this runs; `finish()` is never reached.
- Front end ignores `systemMessage`: the stderr line and the log line still exist; the owner reads the log.
- A hook emitting JSON on stdout with exit 0 that the front end cannot parse: the shape is one object with one
  string key, produced by `jq -n`; the `ask()` JSON at `:80` already relies on the same channel.
- `git log` fails in `has_agent_trailer` (shallow clone, unknown base): `2>/dev/null` and `grep -q` return
  non-zero, the PR is treated as not trailer-authored, and the earlier `git diff` at `:37-42` already exited 1
  for an unresolvable base. Surfaces as the existing `could not diff` message.
- A commit body containing the trailer text inside a quoted paste: false positive, the PR needs the label; the
  cost is one human label, the same as today for any `claude/` branch.

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: `ask()` in `production-gate.sh:188` puts the whole command in its reason, which now lands in the log; a command that carried a secret literal would be logged (block-secrets.sh blocks it in the same PreToolUse round, but each hook writes its own line) — policy: security-standards 1 and 7 — contradiction? no — owner: luissiviero — resolution: the same text is already in the transcript; the log is git-ignored and local; accept, and note in `.sdlc/README.md` that the log is not for sharing.
- C2: the hook process writes under `.sdlc/`, which rule 3 says agents never edit — policy: CLAUDE.md rule 3 / `.sdlc/README.md:1` — contradiction? no — owner: luissiviero — resolution: the write is by the guard, not by an agent tool call, and the log path is on the never-unlock list so no tool call can touch it; reword `.sdlc/README.md:1`.
- C3: the agent that authors a control-plane PR can also apply `control-plane-approved` through `gh` under the owner's login (consensus row 24) — policy: security-standards 8 — contradiction? yes (residual) — owner: luissiviero — resolution: out of scope here; documented in `control-plane-label.md`; the owner's review under CODEOWNERS and branch protection remain the gate against intent.
- C4: trailer detection depends on the session leaving trailers; an agent commit without them on a `work/` branch is still human to CI — policy: `control-plane-label.md:32-34` — contradiction? no — owner: luissiviero — resolution: prefixes plus trailers are belt and braces, not proof; the doc says so; the hook and the log are the local record.
- C5: whether `systemMessage` renders for an exit-0 PreToolUse hook is unverified (A2) — policy: `docs/sdlc/README.md` hook contract — contradiction? no — owner: luissiviero — resolution: log file is the primary channel; the owner checks rendering once after the session restart and records the answer in the deviations log.

## Open questions carried from intent.md
- Does the front end in use render `systemMessage` for an exit-0 PreToolUse hook? (C5)
- From this item on, the kit's own control-plane PRs need the owner's label to go green; accepted?

## Decisions (ADR-style: context → decision → consequences)
- D1: context: the promised audit trail was stderr on exit 0 → decision: a file is the primary channel, the systemMessage secondary, the stderr line kept for the existing tests → consequences: every decision is greppable with a timestamp and session id; `docs/sdlc/metrics.md:25` gains a source.
- D2: context: an exit-0 JSON could carry `permissionDecision: allow` → decision: never; only `systemMessage` → consequences: the tool's own permission prompt is never suppressed by the kit.
- D3: context: the owner chose to keep the committed unlock rather than move it to the launching shell → decision: make CI recognise the kit's own PRs by prefix list and trailer instead → consequences: each kit control-plane PR needs the owner's label; `docs/sdlc/README.md:108` changes from "claude/*" to "agent-authored (prefix or trailer)".
- D4: context: `release-authorizations/`, `approvers.yaml` and the new log are the three files whose integrity the other gates rest on → decision: hard-coded never-unlock list in `protect-paths.sh` (A5), not a config key → consequences: no config line can widen it; the release-gate and approval-gate items rely on it.
- D5: context: WI-5 and WI-6 need `fm_value`, `artifact_role`, `approver_has_role` → decision: land them here, additive and tested, with no caller → consequences: one `_lib.sh` change per item, serial landing.

## Gotchas found while reading the codebase
- `knowledge/decisions/self-hooks-on.md:55` (cited by the plan) is the stale "(none exist here yet)" about `PLAN_REQUIRED_PATHS`, now `scripts` (`.sdlc/config.env:4`); the audit-trail claim to fix is at `:59-61`. Fix both.
- The plan's A2 evidence says 54 of 95 commits carry `Co-Authored-By: Claude` and 24 `Claude-Session:`; at `89bcf9a` the tree has 96 commits, 55 and 25. One commit newer; the point stands.
- `test_bash_plan_gates.py:172-176` asserts empty stderr for an unprotected Edit under the unlock, so `finish()` must print nothing when `UNLOCKED` is empty; stdout must stay empty too (`hooktest.py:9-11`).
- `test_control_plane_hardening.py:23-28` payloads carry no `session_id`, so those lines log `?`; `test_bash_plan_gates.py:39` and the fixtures do carry `test-session`.
- `scripts/run_evals.sh:51` unsets the unlock, and `hook-unlock-covers-edit-branch.yaml:8` runs the hook with `CLAUDE_PROJECT_DIR="$R"`, the real repo; the new eval must use a `mktemp -d` repo with `.sdlc/config.env` copied (the pattern in `ci-control-plane-label-exempts.yaml:5-7`) so it never appends to this repo's live log.
- `test_check_control_plane.py:19-53` commits carry no trailers and author `test`, so the existing six tests stay valid under R-7; the trailer tests add commits whose message body carries the trailer line.
- `is_agent_branch` (`check_control_plane.sh:66-74`) matches `"$prefix"*`, so entries keep their trailing slash and the config value must be one quoted, space-separated string.
- `.gitignore` gains `monitoring/series/` because `bands.yml:52-53` writes `monitoring/series/<metric>.txt` in CI; the plan lists the line without the reason.
- CLAUDE.md line 68 sits after `<!-- END GENERATED -->` (`:65`), so it is hand-edited and `context-drift.sh` (which runs `gen_context_files.py --check`) does not regenerate it.
- `docs/sdlc/README.md:74` lists the hooks and `check_plugin_manifest.py:286` requires every hook path to be executable; no new hook file here, so neither changes.

## Not doing
- Adding `.claude/settings.json` to `PROTECTED_PATHS` (consensus row 13, last sentence): a later item, since it changes what an adopter's agent may edit.
- Gating `gh pr edit --add-label` or any label mutation from a session (C3).
- Log rotation, an OTel exporter, or a metrics script that reads the log; `sdlc_metrics.py` may consume it later.
- Any change under `.github/workflows/` or to the Gemini wiring; Gemini ignores `systemMessage` and the log line still lands.
- Calling `fm_value` from `require-plan.sh` or `protect-tests.sh`; that is the front-matter item's plan.
