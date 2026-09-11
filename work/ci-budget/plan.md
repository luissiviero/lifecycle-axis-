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
intent's Q2 names. Two departures, and both are from the **approved spec**, not only from the guide, so the
owner is deciding them when they tap this plan:
- the spec's Design names `claude/ci-budget-control-plane` and `claude/ci-budget-agent-side`; this plan uses
  one branch, reset between the two pull requests. The ledger's `PR #<n>` lines will carry that branch name,
  which is this session's, not the item's;
- the spec's D7 says the owner switches the session to Fable at each milestone; this plan runs each milestone
  under the existing `plan-reviewer` and `security-reviewer` roles with Fable passed as the model at launch.
  Those role files carry no `model:` key, so the model is a pin the caller supplies; what they do carry is a
  `tools:` list with no `Edit`, `Write` or `MultiEdit`, which is what rule 8 and
  `knowledge/decisions/one-writer-until-ledger.md` mean by read-only, and what keeps one writer per item.

The writer is this session on Opus; the reviewers are Sonnet subagents under the same two roles.

## Files that change
Every path that will change. Globs allowed. CI fails the PR if the diff touches anything else.
- .github/workflows/sdlc-gate.yml — R1 `ready_for_review`, the draft and Bot-edit job guard, per-pull-request concurrency; R2 both triage steps behind the `triage` label; header comment
- .github/workflows/pr-review.yml — R3 concurrency, the `local` head-repository guard, which gates the checkout step's own `if:` rather than only reporting beside it, the pin step extended to `.claude/`, `CLAUDE.md`, `GEMINI.md`, `AGENTS.md` on the comment route; header comment. The guard adds one API call, `gh api repos/<repo>/pulls/<n>`, covered by the `pull-requests: write` this workflow already holds; the permissions comment gains that surface by name
- .github/workflows/agent-evals.yml — R4 `schedule` and `workflow_dispatch` only, `hook-cases` deleted, `full-suite` unconditional; header comment
- .github/workflows/delegated-merge.yml — R5 `workflows: [sdlc-gate, pr-review]` and the comment that counts them; safe because `.sdlc/delegation.yaml`'s `require-checks` already lists those two and not `agent-evals`, and the comment says so, so a later edit cannot restore one list without the other
- scripts/delegated_merge.py — R6 the two `_pr_runs` clauses, and nothing in `check_check_runs`, which the spec keeps out of scope; R7 the `delegation` condition, its place in `run()`, the `keep_going` rule, `_code()` and `finish()`. The script itself gains no GitHub API call, and no `permissions:` block in any of the four workflows changes; `pr-review.yml` does gain one call, named in its own bullet, which is what `knowledge/lessons/workflow-permissions-name-every-api.md` asks to be said out loud
- scripts/test_delegated_merge.py — R6 and R7 cases; the fixture lists moved to the two-name policy (R12 names the seven sites)
- scripts/test_run_evals.py — R4 `AgentEvalsWorkflow` rewritten as five tests
- scripts/test_check_workflow_permissions.py — R1 and R2 into `SdlcGate`; new `PrReviewWorkflow` and `DelegatedMergeWorkflow` classes
- .claude/skills/sdlc-run/SKILL.md — R8 step 3 opens the pull request as a draft; one code pull request at a time
- .claude/skills/sdlc-review/SKILL.md — R8 step 4 marks it ready and asks the owner for the `triage` label
- .claude/skills/sdlc-intent/SKILL.md — R8 step 5 opens the intent pull request as a draft
- evals/cases/skill-opens-drafts.yaml — R8 the hook-kind case that pins those three strings
- evals/README.md — R13 the sentence that says when cases run, stale once R4 removes the pull-request trigger; not covered by the chain check's exempt list, so it is listed here
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
2. `pr-review.yml`: the `local` guard gating the checkout, the four step conditions, the concurrency group, and the pin step extended to the agent-config files. It is written first because it is the change most likely to need a second round, not because writing it first shortens the exposure: PR-A merges as one unit, so the fork route is open until the owner's click whatever the internal order. Reaching `main` sooner would mean a pull request of its own, which the spec does not ask for and which the owner can call for at the tap; the route needs a member or collaborator to type `@claude` on a fork pull request, which is why it rides here. Verifiable: those `PrReviewWorkflow` tests pass; `scripts/checks/workflow-yaml.sh` and `workflow-permissions.sh` pass; `grep -n "head_repository\|head.repo" .github/workflows/pr-review.yml` shows the guard reached by the checkout step's own `if:`, not a step that only reports beside it.
3. `sdlc-gate.yml` (R1, R2), `agent-evals.yml` (R4), `delegated-merge.yml` (R5). Verifiable: `python3 -m unittest scripts.test_check_workflow_permissions scripts.test_run_evals` green; the two workflow checks green.
4. `scripts/delegated_merge.py` R6, then R7, each with its cases from the spec's third column, and three invariants the diff must satisfy rather than merely not break:
   - after `_pr_runs` filters, at least one `success` run of each required workflow remains, which `check_required_runs`'s empty-`matching` refusal already enforces and `::test_only_a_cancelled_run_is_refused` pins from the other side: dropping is never allowed to turn "nothing passed" into "nothing failed";
   - the rule stays inside `_pr_runs`, as spec R6, D2 and C1 require. An earlier draft of this plan also carried it into `check_check_runs`, which reads the commit's check-run rows and does not accept `cancelled`; M1 withdrew that, on two grounds. It contradicts an approved spec, which is the owner's to amend and re-tap, not the plan's to widen. And its premise is unverified: that call passes no `filter`, so GitHub's default `latest` applies, and an evicted attempt's row may never be returned once a later run of the same name exists, which would make the clause dead code that still widens acceptance for any app's `cancelled` row. If PR-A's end-to-end case shows the deadlock is real, that is a deviation logged with the evidence and carried to the owner, not a silent addition;
   - the `delegation` condition defers to `grant` whenever the base intent's `status` is `delegated`: that is an agent having signed its own grant, which `check_grant_front_matter` refuses red, and R7 must never fold it into a green `not-delegated` run.
   Verifiable: `python3 -m unittest scripts.test_delegated_merge` green, including `DelegationCondition::test_self_signed_intent_defers_to_the_grant_condition` for the third invariant, which no case in the spec's column covers; `git diff origin/main -- scripts/test_delegated_merge.py` shows no removed `def test_`; `scripts/test_check_artifact_chain.py` untouched.
5. R13's sentences in the six documents, `evals/README.md` and the three workflow headers. Verifiable by content, since `check_okf.py` reads front matter and links rather than prose: `grep -n "agent-evals" docs/sdlc/github-setup.md docs/sdlc/README.md evals/README.md` names it only as the nightly and never as a pull-request trigger or a required check; `grep -n "control-plane-approved\|triage" docs/sdlc/github-setup.md` finds a bullet saying the label must exist, which is new text rather than the word `triage` the file already carries at `:89`; then `python3 scripts/check_okf.py` ends `0 warnings`.
6. Regenerate, verify, commit, chain check, push. Sonnet `plan-reviewer` and `security-reviewer` over the diff; then the Fable milestone revision M2; fixes pushed; `gh pr ready` is unavailable in this container, so the pull request is marked ready through the GitHub tool and the ledger records `PR #<n> | draft -> in-review`. The owner creates the `triage` label, applies `control-plane-approved` after reading the workflow diff, decides branch protection, and merges. Fable M3 after the merge-conditions dry run.
7. PR-B opens as a draft on the branch reset from the merged `main`. R8: the three skills and `evals/cases/skill-opens-drafts.yaml`. Verifiable: `scripts/run_evals.sh --only skill-names-match-templates` and `--only skill-opens-drafts` both pass, the second failing before the skills change, since `gh pr ready` is already in `sdlc-review` today and only `--draft` in `sdlc-run` and `sdlc-intent` is new.
8. R9: the new bullet in `docs/sdlc/rules/30-conventions.md` paid for by re-flowing the reviewer-model bullet, measured against the adopter's render before anything is committed. Verifiable: `grep -c "one agent code pull request" CLAUDE.md GEMINI.md AGENTS.md` is 1 each, which proves the bullet exists rather than only that the cap holds; then `bash scripts/adopt.sh "$SCRATCH/adopt"`, `python3 scripts/gen_context_files.py --root "$SCRATCH/adopt"` and `wc -l "$SCRATCH/adopt/CLAUDE.md"` print 120 with no "over MAX_CONTEXT_LINES"; then `python3 scripts/gen_context_files.py` here and `scripts/checks/context-drift.sh` passes.
9. R10: `ActionsMinutesSeries` failing first, then the series and `_billed_minutes`, then the fixture, then the band and the third-metric assertion. Verifiable: `python3 -m unittest scripts.test_github_metrics scripts.test_bands_config`; `python3 scripts/github_metrics.py actions_minutes_per_pr --from-json scripts/fixtures/gh_runs_minutes.json` prints `5.000000` then `2.000000`, the six-decimal form of `github_metrics.py:182`; `python3 scripts/bands_config.py` prints 3 rows.
10. R11: the decision record and its index line. Verifiable: `python3 scripts/check_okf.py` `0 warnings`; the index names it once.
11. R13's handoff section, carrying the one-session-per-item protocol and the seed prompt for the next session. Verifiable: `scripts/checks/front-matter.sh` and `okf.sh` pass.
12. Regenerate, verify, commit, chain check, push, reviewers, Fable M4, ready, ledger line, owner's merge click.
13. One week after PR-A merges: the seven acceptance numbers of spec R14 on real runs, Fable M5 over them, a closing ledger line, then the owner retires the item.

## Risks
- Risk: a `cancelled` run lands on a ready head sha with no push, because GitHub evicts a pending run when a third event joins its concurrency group → mitigation: R6(ii) ignores a `cancelled` run only under a later success of the same workflow on the same sha, with three cases pinning both directions; a `cancelled` run with no later success still refuses.
- Risk: the `not-delegated` verdict hides a refusal that is about the pull request rather than the grant → mitigation: R7 keeps `pull-request` and `locked-paths` evaluated and red, and maps exit 0 only when `not-delegated` is the sole non-`ok` line.
- Risk: R6 clears the deadlock in the two conditions that read `_pr_runs`, and `check_check_runs` may still refuse on an evicted attempt's check-run row, which would leave the pull request unmergeable for the same reason the change exists to remove → mitigation: none in this plan, deliberately. The spec confines the rule to `_pr_runs`, the premise is unverified (the call takes GitHub's default `latest` filter, which may never return the superseded row), and the failure mode is fail-closed: a refusal, never a merge. Step 4's end-to-end case is what would expose it, and if it does the deviation goes to the owner with the evidence, since widening it is a spec change.
- Risk: the `not-delegated` verdict masks the one refusal that matters most, an intent an agent signed for itself → mitigation: step 4's third invariant defers to `grant` on a `delegated` intent status, so a self-signed grant stays a red run with its own condition line.
- Risk: the reviewer on the `@claude` comment route reads its own instructions from the head branch → mitigation: the pin step restores the agent-config files from base, the same mechanism that already pins `REVIEW.md`.
- Risk: the measure counts the runs this change creates, since a skipped run bills nothing but scores the one-minute floor → mitigation: R10 excludes `skipped` from the sum, and the fixture proves it.
- Risk: the new convention line pushes the adopter's rendered context file over `MAX_CONTEXT_LINES`, at which point `gen_context_files.py` writes nothing at all → mitigation: step 8 measures the adopter render before the commit, and the bullet is paid for by re-flowing prose, never by dropping a rule.
- Risk: R6 and R7 widen the only control there is. The intent's risk class rests on "two independent controls", but `main` carries no branch-protection rule today (spec C2), so the merge script's own `require-checks` and the owner's click are the whole of it → mitigation: the cases named in R6 and R7 are therefore not a convenience but the control itself, and both changes land in a pull request the owner reads before labelling; creating a protection rule (the guide's optional click 8) would restore the second control and is recorded there, never listing `agent-evals`.
- Risk: PR-A writes to `PROTECTED_PATHS` from an agent session under the control-plane unlock (spec C3) → mitigation: every such write is logged to `.sdlc/hook-decisions.log`, `check_control_plane.sh` blocks the pull request until a human applies `control-plane-approved`, and the label is applied only after the owner reads the workflow diff.
- Risk: a Linux-only failure now surfaces at ready rather than on the first push → mitigation: the ready gate run, and the local verify the agent runs at every step.
- Risk: a required status check that never reports would block every merge → mitigation: `agent-evals` is never a required check, and the merge script refuses rather than waits when a required workflow has no run.
- Risk: the intent's "at most 6 billed minutes" is the floor this change reaches, not a ceiling it holds under: after both pull requests a ready push bills one gate minute, three review minutes and one minute for each of the two merge wakes, which is exactly 6, so a review past its three-minute median, or any push after ready, exceeds it → mitigation: none available in this item, which is why the number is reported with its two assumptions in the closing ledger line rather than claimed as a bound; the mean of at most 10 absorbs the variance and is the number to judge by.
- Risk: R7 is read as a saving. It is not: the merge wake bills its minute whether the verdict is red or green, and on an owner branch or a parallel intent pull request the `pull-request` condition still refuses red, so the green run appears only on the active item's agent branch → mitigation: the plan claims R7 under signal, not minutes, and the acceptance numbers attribute no saving to it.
- What this could break: the merge script is the proxy for the human click, so R6 and R7 are the two places where a mistake merges something that should not; both are bounded by tests named in the spec and land in the pull request the owner reads before labelling.
- Options considered and not taken: keying the gate's concurrency group on the head sha instead of the pull request number (loses cancellation of superseded pushes, which is most of the waste); reading only the newest run per workflow (a larger change to the merge conditions than the trigger needs); a paid GitHub plan or a self-hosted runner (the owner's account decision, out of scope on the intent).

## Proof
- `scripts/verify.sh` green, with `env -u GH_TOKEN -u GITHUB_TOKEN` in this container
- Spec rows → tests: R1, R2 → `test_check_workflow_permissions.SdlcGate`; R3 → `PrReviewWorkflow`; R4 → `test_run_evals.AgentEvalsWorkflow`; R5 → `DelegatedMergeWorkflow`; R6 → `test_delegated_merge.Plumbing`, `ChecksCondition`, `ReviewCondition`, `CoolOffCondition`, and an `EndToEnd` case carrying an evicted attempt through the whole pipeline, which is also what would expose the `check_check_runs` question above; R7 → `DelegationCondition` including the self-signed-intent case, `Plumbing`, `EndToEnd`; R8 → `skill-names-match-templates` and `skill-opens-drafts`; R9 → the adopter render at 120 lines, `context-drift.sh` and `scripts/test_adopt.py`; R10 → `ActionsMinutesSeries`, the fixture series `5.000000, 2.000000`, `bands_config.py` printing 3 rows; R11 → `check_okf.py` and the index line; R12 → the two `git diff` assertions; R13 → the two `grep` content checks of step 5, then `check_okf.py` and `verify.sh`; R14 → the acceptance numbers in the closing ledger line
- Manual / browser / screenshot / eval: the Phase 3 acceptance run of spec R14 on a throwaway draft pull request, and the `delegated-merge` dry run on a ready head sha

## Rollback
- Each change reverts on its own line: the `_pr_runs` clauses, the `delegation` condition (map the verdict to `refused` in `_code()`), the job guards, the concurrency blocks, the fork guard and its four step conditions, the band entry. PR-A and PR-B revert independently, and no change is a migration.

## Deviations log (append during implementation; same commit as the deviation)
- 
