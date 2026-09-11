---
type: sdlc/plan
id: ci-budget
title: Reduce GitHub minutes, waiting time and wasted tokens; keep the crucial procedures, loosen the rest
description: "Two pull requests on one branch: the control plane (gate, review, evals and merge workflows plus the two merge-script rules) then the agent side (draft-first skills, the rule line, the actions_minutes_per_pr measure and its band, the decision record, the handoff)."
stage: build
# status: draft | in-review | approved | delegated | superseded  (require-plan.sh refuses code edits until approved)
status: in-review
# kind: feature | fix  (fix: protect-tests.sh refuses edits to existing test files)
kind: feature
reads: spec.md
# approved-by: engineer for routine; tech lead/architect for medium/high risk; set only by a human
approved-by:
approved-on:
risk-class: low
record:
resource: spec.md
tags: [ci, github-actions, minutes, tokens, latency, drafts, concurrency, delegated-merge, bands]
timestamp: 2026-09-11T16:00:00Z
---
# Plan: reduce GitHub minutes, waiting time and wasted tokens (from intent.md 2026-09-09)

Two pull requests, PR-A (control plane) then PR-B (agent side), each opened as a draft and each ending in
the owner's merge click. Both run on this session's branch `claude/app-creation-mock-test-w4gf88`, reset
from `main` between them: one agent code pull request open at a time, which is the compensating control the
intent's Q2 names. That replaces the guide's two branch names and is the only departure from
`implementation-plan.md`; the writer is this session on Opus, the reviewers are Sonnet subagents, and each
milestone revision is a read-only Fable subagent rather than a session switch, which keeps one writer per
item (`knowledge/decisions/one-writer-until-ledger.md`).

## Files that change
Every path that will change. Globs allowed. CI fails the PR if the diff touches anything else.
- .github/workflows/sdlc-gate.yml — R1 `ready_for_review`, the draft and Bot-edit job guard, per-pull-request concurrency; R2 both triage steps behind the `triage` label; header comment
- .github/workflows/pr-review.yml — R3 concurrency, the `local` head-repository guard before the checkout, the pin step extended to `.claude/`, `CLAUDE.md`, `GEMINI.md`, `AGENTS.md` on the comment route; header comment
- .github/workflows/agent-evals.yml — R4 `schedule` and `workflow_dispatch` only, `hook-cases` deleted, `full-suite` unconditional; header comment
- .github/workflows/delegated-merge.yml — R5 `workflows: [sdlc-gate, pr-review]` and the comment that counts them
- scripts/delegated_merge.py — R6 the two `_pr_runs` clauses; R7 the `delegation` condition, its place in `run()`, the `keep_going` rule, `_code()` and `finish()`
- scripts/test_delegated_merge.py — R6 and R7 cases; the fixture lists moved to the two-name policy (R12 names the seven sites)
- scripts/test_run_evals.py — R4 `AgentEvalsWorkflow` rewritten as five tests
- scripts/test_check_workflow_permissions.py — R1 and R2 into `SdlcGate`; new `PrReviewWorkflow` and `DelegatedMergeWorkflow` classes
- .claude/skills/sdlc-run/SKILL.md — R8 step 3 opens the pull request as a draft; one code pull request at a time
- .claude/skills/sdlc-review/SKILL.md — R8 step 4 marks it ready and asks the owner for the `triage` label
- .claude/skills/sdlc-intent/SKILL.md — R8 step 5 opens the intent pull request as a draft
- evals/cases/skill-opens-drafts.yaml — R8 the hook-kind case that pins those three strings
- docs/sdlc/rules/30-conventions.md — R9 one bullet in, the reviewer-model bullet re-flowed to pay for it
- CLAUDE.md — R9 regenerated
- GEMINI.md — R9 regenerated
- AGENTS.md — R9 regenerated
- scripts/github_metrics.py — R10 the `actions_minutes_per_pr` series, `_billed_minutes`, `--default-branch`
- scripts/test_github_metrics.py — R10 `ActionsMinutesSeries`
- scripts/fixtures/gh_runs_minutes.json — R10 the fixture the series is proved against
- monitoring/bands.yaml — R10 the band
- scripts/test_bands_config.py — R10 three GitHub metrics instead of two
- knowledge/decisions/ci-budget-crucial-and-loosened.md — R11 what is crucial, what was loosened, each control
- knowledge/decisions/index.md — R11 one line
- docs/sdlc/README.md — R13 the gate row, the evals row, the regression-test row, the protect-main step
- docs/sdlc/github-setup.md — R13 required checks, the triage bullet, the delegated-mode waits
- knowledge/decisions/merge-click-is-the-gate.md — R13 the required-checks list and the public-repository note
- knowledge/decisions/control-plane-label.md — R13 the trigger sentence and the triage route
- docs/sdlc/spikes/pr-review-identity.md — R13 the required-checks checklist
- docs/sdlc/spikes/prompt-surfaces.md — R13 the `paths:` proposal is moot
- docs/sdlc/handoff/HANDOFF.md — R13 a new `## Task state` section; the old heading suffixed `— HISTORY`
- work/ci-budget/plan.md — this file, and its deviations log
- work/ci-budget/log.md — a ledger line at every gate
- work/ci-budget/index.md — regenerated
- work/index.md — regenerated

## Release-gated
Paths under RELEASE_GATED_PATHS with a named human owner (leave "(none)" if none).
- (none)

## Order of work (each step independently verifiable)
1. PR-A opens as a draft on the reset branch, body carrying `Work-Item: ci-budget`. Write the failing tests first: `SdlcGate` gains R1 and R2 cases, new `PrReviewWorkflow` and `DelegatedMergeWorkflow` classes carry R3 and R5, and `AgentEvalsWorkflow` is rewritten for R4. Verifiable: `python3 -m unittest scripts.test_check_workflow_permissions scripts.test_run_evals` fails on exactly those names.
2. `pr-review.yml` first, because A2b is the one open exposure on a public repository: the `local` guard step before the checkout, the four step conditions, the concurrency group, and the pin step extended to the agent-config files. Verifiable: those `PrReviewWorkflow` tests pass; `scripts/checks/workflow-yaml.sh` and `workflow-permissions.sh` pass.
3. `sdlc-gate.yml` (R1, R2), `agent-evals.yml` (R4), `delegated-merge.yml` (R5). Verifiable: `python3 -m unittest scripts.test_check_workflow_permissions scripts.test_run_evals` green; the two workflow checks green.
4. `scripts/delegated_merge.py` R6, then R7, each with its cases from the spec's third column. Verifiable: `python3 -m unittest scripts.test_delegated_merge` green; `git diff origin/main -- scripts/test_delegated_merge.py` shows no removed `def test_`; `scripts/test_check_artifact_chain.py` untouched.
5. R13's sentences in the six documents and the three workflow headers. Verifiable: `python3 scripts/check_okf.py` ends `0 warnings`.
6. Regenerate, verify, commit, chain check, push. Sonnet `plan-reviewer` and `security-reviewer` over the diff; then the Fable milestone revision M2; fixes pushed; `gh pr ready` is unavailable in this container, so the pull request is marked ready through the GitHub tool and the ledger records `PR #<n> | draft -> in-review`. The owner creates the `triage` label, applies `control-plane-approved` after reading the workflow diff, decides branch protection, and merges. Fable M3 after the merge-conditions dry run.
7. PR-B opens as a draft on the branch reset from the merged `main`. R8: the three skills and `evals/cases/skill-opens-drafts.yaml`. Verifiable: `scripts/run_evals.sh --only skill-names-match-templates` and `--only skill-opens-drafts` both pass.
8. R9: the new bullet in `docs/sdlc/rules/30-conventions.md` paid for by re-flowing the reviewer-model bullet, measured against the adopter's render before anything is committed. Verifiable: `bash scripts/adopt.sh "$SCRATCH/adopt"` then `python3 scripts/gen_context_files.py --root "$SCRATCH/adopt"` then `wc -l "$SCRATCH/adopt/CLAUDE.md"` prints 120 with no "over MAX_CONTEXT_LINES"; then `python3 scripts/gen_context_files.py` here and `scripts/checks/context-drift.sh` passes.
9. R10: `ActionsMinutesSeries` failing first, then the series and `_billed_minutes`, then the fixture, then the band and the third-metric assertion. Verifiable: `python3 -m unittest scripts.test_github_metrics scripts.test_bands_config`; `python3 scripts/github_metrics.py actions_minutes_per_pr --from-json scripts/fixtures/gh_runs_minutes.json` prints `5.0` then `2.0`; `python3 scripts/bands_config.py` prints 3 rows.
10. R11: the decision record and its index line. Verifiable: `python3 scripts/check_okf.py` `0 warnings`; the index names it once.
11. R13's handoff section, carrying the one-session-per-item protocol and the seed prompt for the next session. Verifiable: `scripts/checks/front-matter.sh` and `okf.sh` pass.
12. Regenerate, verify, commit, chain check, push, reviewers, Fable M4, ready, ledger line, owner's merge click.
13. One week after PR-A merges: the seven acceptance numbers of spec R14 on real runs, Fable M5 over them, a closing ledger line, then the owner retires the item.

## Risks
- Risk: a `cancelled` run lands on a ready head sha with no push, because GitHub evicts a pending run when a third event joins its concurrency group → mitigation: R6(ii) ignores a `cancelled` run only under a later success of the same workflow on the same sha, with three cases pinning both directions; a `cancelled` run with no later success still refuses.
- Risk: the `not-delegated` verdict hides a refusal that is about the pull request rather than the grant → mitigation: R7 keeps `pull-request` and `locked-paths` evaluated and red, and maps exit 0 only when `not-delegated` is the sole non-`ok` line.
- Risk: the reviewer on the `@claude` comment route reads its own instructions from the head branch → mitigation: the pin step restores the agent-config files from base, the same mechanism that already pins `REVIEW.md`.
- Risk: the measure counts the runs this change creates, since a skipped run bills nothing but scores the one-minute floor → mitigation: R10 excludes `skipped` from the sum, and the fixture proves it.
- Risk: the new convention line pushes the adopter's rendered context file over `MAX_CONTEXT_LINES`, at which point `gen_context_files.py` writes nothing at all → mitigation: step 8 measures the adopter render before the commit, and the bullet is paid for by re-flowing prose, never by dropping a rule.
- Risk: a Linux-only failure now surfaces at ready rather than on the first push → mitigation: the ready gate run, and the local verify the agent runs at every step.
- Risk: a required status check that never reports would block every merge → mitigation: `agent-evals` is never a required check, and the merge script refuses rather than waits when a required workflow has no run.
- What this could break: the merge script is the proxy for the human click, so R6 and R7 are the two places where a mistake merges something that should not; both are bounded by tests named in the spec and land in the pull request the owner reads before labelling.
- Options considered and not taken: keying the gate's concurrency group on the head sha instead of the pull request number (loses cancellation of superseded pushes, which is most of the waste); reading only the newest run per workflow (a larger change to the merge conditions than the trigger needs); a paid GitHub plan or a self-hosted runner (the owner's account decision, out of scope on the intent).

## Proof
- `scripts/verify.sh` green, with `env -u GH_TOKEN -u GITHUB_TOKEN` in this container
- Spec rows → tests: R1, R2 → `test_check_workflow_permissions.SdlcGate`; R3 → `PrReviewWorkflow`; R4 → `test_run_evals.AgentEvalsWorkflow`; R5 → `DelegatedMergeWorkflow`; R6 → `test_delegated_merge.Plumbing`, `ChecksCondition`, `ReviewCondition`, `CoolOffCondition`; R7 → `DelegationCondition`, `Plumbing`, `EndToEnd`; R8 → `skill-names-match-templates` and `skill-opens-drafts`; R9 → the adopter render at 120 lines and `context-drift.sh`; R10 → `ActionsMinutesSeries`, the fixture series `5.0, 2.0`, `bands_config.py` printing 3 rows; R11 → `check_okf.py` and the index line; R12 → the two `git diff` assertions; R13 → `check_okf.py` and `verify.sh`; R14 → the acceptance numbers in the closing ledger line
- Manual / browser / screenshot / eval: the Phase 3 acceptance run of spec R14 on a throwaway draft pull request, and the `delegated-merge` dry run on a ready head sha

## Rollback
- Each change reverts on its own line: the `_pr_runs` clauses, the `delegation` condition (map the verdict to `refused` in `_code()`), the job guards, the concurrency blocks, the fork guard and its four step conditions, the band entry. PR-A and PR-B revert independently, and no change is a migration.

## Deviations log (append during implementation; same commit as the deviation)
- 
