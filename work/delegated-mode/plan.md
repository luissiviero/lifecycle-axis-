---
type: sdlc/plan
id: delegated-mode
title: A second way to run a work item, where I approve the start and the AI signs the rest under its own name
description: "Files, order, proof and risks for delegated mode across four pull requests: vocabulary and chain check, hooks and signing script, prose and skills, and the CI merge workflow."
stage: build
status: approved
kind: feature
reads: spec.md
approved-by: luissiviero
approved-on: 2026-09-05
risk-class: low
record:
resource: https://github.com/luissiviero/lifecycle-axis-/issues/40
tags: [delegation, approvals, hooks, chain-check, auto-merge, policy, control-plane]
timestamp: 2026-09-05T11:28:24Z
---
# Plan: a second way to run a work item, where I approve the start and the AI signs the rest under its own name (from intent.md 2026-09-05)

## Files that change
Pull request 1a, vocabulary (no hooks, no label):
- scripts/delegation.py — new; loads `.sdlc/delegation.yaml` through `approvers._parse` (spec R-1, D1)
- scripts/approvers.py — `_parse` takes the allowed top keys as a parameter; no behaviour change for approvers (D1)
- scripts/check_artifact_chain.py — `delegated` status, grant check, signature check, revision and deviation rules, empty-slug message (R-2, R-4, R-5, R-6)
- scripts/gen_index.py — renders `delegated` with its signer (R-2)
- scripts/log_ledger.py — `signatures(entries, artifact)` twin of `approvals` (R-2)
- scripts/test_delegation.py — new (R-1)
- scripts/test_check_artifact_chain.py — class `DelegatedChain`, `test_empty_active_slug_is_one_clear_failure` (R-4, R-5, R-6)
- scripts/test_approval_author.py — grant-commit author cases (R-4)
- scripts/test_gen_index.py — delegated rendering (R-2)
- scripts/test_log_ledger.py — `signatures` (R-2)
- scripts/adopt.sh — copies the policy template; blanks `delegated-by` and `delegated-on` on the example (R-3)
- scripts/test_adopt.py — the copied example carries `mode: supervised` and empty grant keys (R-3)
- docs/sdlc/templates/intent.md — `risk-class`, `mode`, `delegated-by`, `delegated-on` (R-3, D2)
- docs/sdlc/templates/spec.md — status comment lists `delegated` (R-2)
- docs/sdlc/templates/plan.md — status comment lists `delegated` (R-2)
- docs/sdlc/templates/incident.md — status comment lists `delegated` (R-2)
- docs/sdlc/templates/log.md — example `-> delegated` line (R-2)
- docs/sdlc/templates/delegation.yaml — new; the policy file adopters copy (D1)
- docs/sdlc/templates/revision.md — new; the consensus record (D4)
- work/_example/intent.md — the four new keys (R-3)
- docs/sdlc/rules/00-chain.md — status enumeration (R-2)
- docs/sdlc/rules/60-lessons.md — pointer to `workflow-permissions-name-every-api.md` (R-12)
- CLAUDE.md — regenerated
- GEMINI.md — regenerated
- AGENTS.md — regenerated
- knowledge/lessons/ledger-slot-holds-status-only.md — status enumeration (R-2)
- knowledge/decisions/delegated-mode.md — new; amends and supersedes as spec C1 and C2 say (R-13)
- knowledge/decisions/human-only-approvals.md — one pointer line to the new record (R-13)
- knowledge/decisions/merge-click-is-the-gate.md — one pointer line: superseded for delegated items (R-13)
- knowledge/decisions/index.md — the new record
- work/index.md — regenerated
Pull request 1b, the act (label: hooks, settings):
- .claude/hooks/_lib.sh — `policy_value`, `policy_list`, `agent_handle_ok`, `intent_mode`, `delegation_on` (R-10)
- .claude/hooks/protect-paths.sh — `.sdlc/delegation.yaml` on the never-unlock list (R-10)
- .claude/hooks/protect-approvals.sh — `check_result` decides on the whole resulting front matter; Bash branch reads `mode`, allows `sign.py`, refuses mutating `gh api` on `contents/` and `git/` (R-9, D5)
- .claude/hooks/require-plan.sh — the `delegated` branch (R-10)
- scripts/sign.py — new (R-7, D3)
- scripts/approve.py — `--delegate` (R-8)
- scripts/test_sign.py — new (R-7)
- scripts/test_approve.py — `--delegate` cases (R-8)
- scripts/test_protect_approvals.py — class `Delegated` (R-9)
- scripts/test_hooks_baseline.py — require-plan delegated cases (R-10)
- scripts/test_lib_helpers.py — the five helpers (R-10)
- scripts/test_protect_paths_bash.py — never-unlock entry (R-10)
- evals/cases/sign-refuses-without-grant.yaml — new (R-7)
- evals/cases/sign-refuses-human-handle.yaml — new (R-7)
- evals/cases/sign-refuses-intent.yaml — new (R-7)
- evals/cases/sign-refuses-when-policy-off.yaml — new (R-7)
- evals/cases/sign-refuses-resign-without-revision.yaml — new (R-7)
- evals/cases/hook-allows-delegated-sign.yaml — new (R-9)
- evals/cases/hook-refuses-mode-edit.yaml — new (R-9)
- evals/cases/hook-refuses-new-intent-with-grant.yaml — new (R-9)
- .claude/settings.json — five allow entries (R-11)
- docs/sdlc/templates/claude-settings.json — the same five entries (R-11)
- .sdlc/delegation.yaml — created by the owner on `main` from the template, never by the session; listed so the chain check accepts the owner's commit if it rides this branch instead
Pull request 1c, prose (no label):
- .claude/skills/sdlc-intent/SKILL.md — asks the mode, writes `mode: supervised` and `risk-class` (R-12)
- .claude/skills/sdlc-spec/SKILL.md — sign and continue when delegated (R-12)
- .claude/skills/sdlc-plan/SKILL.md — same, plus the deviation and revision rule (R-12)
- .claude/skills/sdlc-review/SKILL.md — the summary line (R-12)
- .claude/skills/sdlc-incident/SKILL.md — sign and continue when delegated (R-12)
- .claude/skills/sdlc-run/SKILL.md — new; grant to ready pull request; the revision rule verbatim (R-12)
- docs/sdlc/rules/10-hard-rules.md — one line: `delegated` under a grant; `approved` stays human (R-12)
- docs/sdlc/rules/30-conventions.md — one line: sign with `scripts/sign.py`; ledger vocabulary (R-12)
- docs/sdlc/rules/40-claude-only.md — one line: `/sdlc-run` (R-12)
- docs/sdlc/rules/50-gemini-only.md — one line: the same skill text (R-12)
- docs/sdlc/README.md — three enforcement-matrix rows and the policy file (R-13)
- REVIEW.md — `Important: <n> | Nits: <m>` in the format block (R-13)
- docs/sdlc/github-setup.md — the grant routine; signing a local grant commit (R-13)
- .sdlc/README.md — `delegation.yaml` in the control-plane list (R-13)
Pull request 2, the merge (label: workflow):
- .github/workflows/delegated-merge.yml — new (R-14, D6)
- scripts/delegated_merge.py — new (R-15)
- scripts/test_delegated_merge.py — new (R-15)
- scripts/check_workflow_permissions.py — allowlist entry; repo-relative comparison (R-14)
- scripts/test_check_workflow_permissions.py — `test_allowlist_matches_relative_path` (R-14)
- docs/sdlc/handoff/HANDOFF.md — task state: the two modes, the policy file, the grant routine
This item's own artifacts:
- work/delegated-mode/intent.md — new; this item
- work/delegated-mode/spec.md — new; this item
- work/delegated-mode/plan.md — new; this item; deviations appended
- work/delegated-mode/log.md — gate ledger, lines appended
- work/delegated-mode/index.md — generated by `gen_index.py`
- .sdlc/active — set to `delegated-mode` by the session on this branch (deviation 1; control plane, so pull request 1a needs the label after all)

## Release-gated
(none)

## Order of work (each step independently verifiable)
1. Preconditions, before any edit: `.sdlc/active` reads `delegated-mode` on `main` (the owner's commit; without it the finished `batch-b-followups` plan would be what authorises the `scripts/` edits below); `python3 scripts/run_tests.py` green on the base, count noted; `git log -1 --format=%h -- .claude/skills` prints `c420e3c`. A difference is recorded under Deviations first.
2. Pull request 1a, tests first: `scripts/test_delegation.py`, `DelegatedChain`, `test_empty_active_slug_is_one_clear_failure` red (the drafts come from a non-Fable subagent writing to the scratchpad from the spec's oracle column; the session reads and applies them). Then `delegation.py`, the chain check, `gen_index.py`, `log_ledger.py` green; templates, example, `adopt.sh`, rules fragments, regeneration, decision record; R-2, R-3, R-6, R-13 oracles; verify; push; owner merges. Owner then creates `.sdlc/delegation.yaml` on `main` from the template.
3. Pull request 1b, from the merged `main`: `_lib.sh` helpers first, tested from a second shell before the hooks use them; then `protect-paths.sh`, `protect-approvals.sh`, `require-plan.sh`, each atomically (stage in the scratchpad, `bash -n`, copy, full `run_tests.py`, revert on failure). Then `sign.py` (drafted by a subagent from R-7, applied by the session), `approve.py --delegate`, tests, evals, settings; R-7 to R-11 oracles; `plan-reviewer` and `security-reviewer` passes; verify; push; ask for the label; owner merges.
4. Pull request 1c: skills, fragments, regeneration under 120 lines, README rows, `REVIEW.md`, setup docs; R-12, R-13 oracles; verify; push; owner merges.
5. Pull request 2: `delegated_merge.py` (drafted by a subagent from R-15, applied by the session) and its fixtures first, red then green; the workflow; the allowlist fix; R-14, R-15 oracles; `--dry-run` against pull request 1c's own head prints the grant refusal; `security-reviewer` pass on the workflow and script; handoff; verify; push; label; owner merges.
6. First live delegated item, after 2 merges: a `scripts/`- or docs-only follow-up (the NUL-byte check, or the flaky eval), granted with `approve.py --delegate --activate`, run with `/sdlc-run` end to end. Not the control-plane tiering item: the merge script refuses protected-path diffs by design.

## Risks
- Risk: a hook edit breaks `_lib.sh` and locks the session out of every tool → mitigation: helpers land first and are exercised from a second shell (`knowledge/lessons/test-lib-changes-from-a-second-shell.md`); each hook edit is atomic with a revert path.
- Risk: the policy file is created before `delegation.py` exists on `main`, or never created → mitigation: nothing on `main` reads it before pull request 1a; a missing file is the closed state, so the order only delays the mode, never opens it.
- Risk: a `delegated` signature passes CI without a valid grant → mitigation: R-4 checks the grant in both chain-check modes; `DelegatedChain` has a fail case for each condition; the merge script checks the grant again server-side.
- Risk: the merge workflow merges something it should not → mitigation: every condition is a separate fixture in `test_delegated_merge.py`; the `locked_paths` refusal keeps the judging code identical on head and main; `sha` on the merge call closes the push race; `--dry-run` is run against a supervised item before the workflow is enabled.
- Risk: the `-G '^mode: delegated$'` author check reads a prose line as the grant → mitigation: the literal never appears in prose in `work/` files (the same rule as for the status line); the spec's example blocks are in `docs/sdlc/templates/`, which the check does not read.
- What this could break: which artifacts CI accepts (one more status, under a grant); which pull requests merge without a click (delegated, low-risk, non-control-plane only); the plan gate (opens on a delegated plan under a grant).
- Options considered and not taken: `approved` with an agent handle (spec D-a); the grant on the plan (D-b); keys in `config.env` (D-c); a revision rule in the skills only (D-d); the session merging with `gh pr merge` (D-e); squash merges (D-f); one large pull request (D-g); a cool-off before merging (intent Q2).

## Proof
- `scripts/verify.sh` green: last line `VERIFY: PASS (<sha>)`, on each of the four pull requests
- Spec rows → tests: R-1 → `test_delegation.py`; R-2 → the greps and `gen_index.py --check`; R-3 → `test_adopt.py`; R-4, R-5 → `DelegatedChain`; R-6 → `test_empty_active_slug_is_one_clear_failure`; R-7 → `test_sign.py` and five evals; R-8 → `test_approve.py`; R-9 → `test_protect_approvals.py::Delegated` and three evals; R-10 → `test_hooks_baseline.py`, `test_lib_helpers.py`, `test_protect_paths_bash.py`; R-11 → the JSON assertion; R-12 → `context-drift.sh`, `plugin-manifest.sh`, the greps, `wc -l`; R-13 → `check_okf.py`, the greps; R-14 → the two workflow checks, `test_allowlist_matches_relative_path`; R-15 → `test_delegated_merge.py`, the `--dry-run`; R-16 → `VERIFY: PASS`, `CHAIN: PASS`, `EVALS: N pass, 0 fail`, `OKF: N docs, 0 warnings`
- Manual / browser / screenshot / eval: step 6, the first live delegated item, merges with no owner action after the grant; its ledger shows every signature under the agent's handle; the merge comment names the grant commit.

## Rollback
- Revert the pull requests in reverse order and delete `.sdlc/delegation.yaml`; supervised mode is untouched throughout, so a partial rollback (for example keeping 1a and reverting 2) leaves a consistent repository where delegated signatures are valid but nothing merges without a click.

## Deviations log (append during implementation; same commit as the deviation)
- 2026-09-05 — step 1: the owner's `.sdlc/active` edit on `main` did not land (two attempts from the phone; `main` still names `batch-b-followups`), while the three approvals did. The session sets `.sdlc/active` to `delegated-mode` on this branch instead, as `batch-b-followups` did. The chain check treats `.sdlc/active` naming this slug as this item's own file; `check_control_plane.sh` does not, so pull request 1a needs `control-plane-approved` for that one line. The precondition's purpose holds: from this commit the plan gate reads this item's approved plan, not the finished one.
- 2026-09-05 — step 2, out of order: CI's `front-matter.sh` went red on the generated `work/delegated-mode/index.md` because `gen_index.py` wrote this item's description, which holds `: `, as a plain YAML scalar. Fixed in `gen_index.py` (`_yaml_scalar`: quote a title or description PyYAML could not read back, leave plain values plain) with a round-trip test; the golden for a title holding `: ` now expects the quoted form, since the old golden pinned invalid YAML. Both files are in the list above for R-2; the fix lands before the rest of pull request 1a because the chain PR was red on it.
- 
