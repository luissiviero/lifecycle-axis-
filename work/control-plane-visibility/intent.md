---
type: sdlc/intent
id: control-plane-visibility
title: Hook decisions must be logged; the control-plane unlock must be visible; CI must recognise the kit's own agent PRs
description: The unlock's audit line goes to stderr on exit 0 where Claude Code never shows it, check_control_plane.sh never matched the kit's kit/* branches, and no hook decision is recorded anywhere durable.
stage: plan
status: in-review
author: Luis Siviero (repo owner), drafted with Claude from the 2026-09-04 playbook comparison
approved-by:
approved-on:
supersedes:
record:
resource: https://claude.ai/code/session_01DSYmeD7eng2GKQ3EbHQDzo
tags: [hooks, control-plane, unlock, audit-log, ci, consensus-item-2, consensus-item-4]
timestamp: 2026-09-04T21:46:58Z
---
# Intent: hook decisions must be logged; the control-plane unlock must be visible; CI must recognise the kit's own agent PRs

## Problem
`knowledge/decisions/self-hooks-on.md:59-61` promises that "every control-plane write by an agent leaves an
audit line in the transcript", and `knowledge/decisions/bash-write-guard.md:77-78` says the line "appears in
the transcript". It does not. `protect-paths.sh:25` prints the unlock line with `>&2` and the hook then
exits 0 (`:37`, `:48`); Claude Code shows a hook's stderr only on exit 2 (`_lib.sh:3`). So every write this
repo's agent makes under `.claude/hooks`, `.github/workflows`, `.sdlc` or `.gemini` (`.sdlc/config.env:7`)
under the committed unlock (`.claude/settings.json:3`) is silent to the owner reading the session.

The CI backstop the same decision record leans on ("CI's `check_control_plane.sh` ... remain the
deterministic gate") never looked at the kit's own PRs. `scripts/check_control_plane.sh:77` treats a PR as
agent-authored only when `SDLC_PR_AUTHOR_TYPE` is `Bot` or the head ref starts with a prefix in
`AGENT_BRANCH_PREFIXES`, whose default at `:35` is `claude/` alone. The kit's PR branches were `kit/*` and
`spike/*` (`git log` still shows `kit/skill-template-drift` and `kit/pr-review-posting` merges), so 11 of the
13 control-plane PRs took the "human-authored, review by CODEOWNERS" path at `:81-85` and were never checked.
`docs/sdlc/README.md:108` still claims "CI blocks any `claude/*`-authored PR touching `PROTECTED_PATHS`".

Nothing records a hook decision anywhere durable. `block()` and `ask()` in `_lib.sh:79-80` write to stderr or
stdout and exit; the unlock line is stderr; no file, no timestamp, no session id. `docs/sdlc/metrics.md:25`
names "hook decisions with timestamps" as the approval-gate metric and there is no source for it. How we
know: the 2026-09-04 comparison reproduced each case against the live hooks (consensus items 2 and 4,
`scratchpad/consensus.md` rows 13 and 24: "keep the decision, fix the implementation"; "a record more than a
lock"). Who is affected: the owner, who cannot see what the unlock let through; every adopter who copies
`check_control_plane.sh` and names branches anything but `claude/*`.

## Proposed outcome
- Every `block`, `ask` and `unlock` decision by any hook appends one tab-separated line (UTC timestamp,
  verdict, hook name, tool, session id, detail) to `.sdlc/hook-decisions.log`, git-ignored; a failed log
  write never changes a verdict.
- A `protect-paths.sh` run that used the unlock ends with one `{"systemMessage": ...}` JSON on stdout
  naming every path written, in addition to the existing stderr line; it never emits `permissionDecision: allow`.
- The unlock never covers `.sdlc/release-authorizations/`, `.sdlc/approvers.yaml` or
  `.sdlc/hook-decisions.log`: a write there is blocked with the unlock set.
- `check_control_plane.sh` treats a PR as agent-authored when its branch starts with a prefix in the new
  `AGENT_BRANCH_PREFIXES` key of `.sdlc/config.env` (default `claude/ kit/ spike/`) or when any commit in
  `base..HEAD` carries a `Co-Authored-By: ... Claude` or `Claude-Session:` trailer. A trailer only on a base
  commit does not count. No workflow change: `sdlc-gate.yml:19` already checks out with `fetch-depth: 0`.
- `_lib.sh` gains `fm_value`, `artifact_role` and `approver_has_role` (for the approval-gate and deploy-gate
  items), reads `cwd` and `session_id` from the hook input, and `FILE` falls back to `notebook_path`; all
  additive, no verdict changes today.
- The docs that describe the audit trail and the CI gate say what the code now does. Test count grows by the
  log, systemMessage, never-unlock, trailer and prefix cases; two new eval cases; `scripts/verify.sh` green.

## Affected users and systems
- Users: the owner (reads the log; labels the kit's control-plane PRs from now on); adopters of the hooks and CI check.
- Services / repos / data: this repo only. `.claude/hooks/_lib.sh` (sourced by every hook),
  `.claude/hooks/protect-paths.sh`, `scripts/check_control_plane.sh`, `.sdlc/config.env`, `.gitignore`,
  the affected tests and evals, `knowledge/decisions/`, `CLAUDE.md`, `docs/sdlc/`, `.sdlc/README.md`.

## Constraints
- Must: keep every hook verdict unchanged for inputs that pass or block today, except the three
  never-unlock paths, which now block under the unlock. Keep the stderr unlock line byte-identical
  (`test_protect_paths_bash.py:170`, `test_bash_plan_gates.py:151,158`, `test_control_plane_hardening.py:111`
  and eval `hook-unlock-covers-edit-branch` assert it).
- Must: stay bash, awk and jq inside hooks (no python3 call); `_lib.sh` edited in one Write, checked with
  `bash -n` and the hook test modules from a second shell before the session's next tool call.
- Must not: emit `permissionDecision: allow` (it would suppress the tool's own permission prompt); log any
  secret material or personal data (the detail field carries the block reason and the path only).
- Must not: edit `.github/workflows/`; treat `work/` as an agent prefix (humans use it).
- Out of scope: the approval-field hook (`protect-approvals.sh`), the Bash write-guard closure, the deploy
  gate, `.claude/settings.json` joining `PROTECTED_PATHS` (consensus row 13's last sentence; a later item).

## Risk class
low — additive helpers and a log file in this repo's tooling; the only stricter verdicts are the three
never-unlock paths. Blast radius is this repo and adopters who copy the hooks. No production data, no
secrets, no deploy path. A bad `_lib.sh` edit can lock the session; the second-shell rule above covers it.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: Does the front end in use render `systemMessage` for an exit-0 PreToolUse hook? Unverified; the log is primary.
  A:
- Q: From this item on, each of the kit's own control-plane PRs needs the owner's `control-plane-approved`
  label to go green. Accepted as the honest state?
  A:
