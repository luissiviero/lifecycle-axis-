---
type: decision
title: What the CI budget loosened, and what stayed crucial
description: "CI on this repository cost about 96 gate runs and 52 review runs of which 89 and 45 were superseded by a later push and paid for in full, plus a triage step averaging 3.6 minutes on a red run. The owner asked for less spend without giving up any control. This record separates the six things that did not move, each naming the file that proves it, from the six that were loosened, each with the control that compensates."
tags: [ci, cost, governance, sdlc, delegated-mode]
timestamp: 2026-09-13T15:45:00Z
---

# What the CI budget loosened, and what stayed crucial

## Context
Three costs, measured before the change (`work/ci-budget/intent.md`): 89 of 96 `sdlc-gate` runs and
45 of 52 `pr-review` runs were superseded by a later push and billed in full; the gate's failure
triage step ran `claude -p` on every red run, 3.6 minutes median and 10.6 at worst, and three of the
last four triaged a drift that was already on `main` and that the pull request body had diagnosed.
`agent-evals` ran the whole suite again on every pull request, duplicating what `verify.sh` already
runs per commit.

The owner's goal was (a) fewer billed minutes, (b) less waiting, (c) fewer wasted tokens — with the
crucial procedures untouched. That last clause is what this record exists to make checkable.

## Decision — crucial, untouched
- **A human approves every chain artifact.** `scripts/approve.py` refuses to run inside an agent
  session and `.claude/hooks/protect-approvals.sh` refuses `status: approved` from an agent; the
  dispatch route records the run's actor. Nothing in this work item touched any of the three.
- **The artifact chain still gates every ready pull request.** `scripts/check_artifact_chain.py`
  runs in `.github/workflows/sdlc-gate.yml` exactly as before; only *when* the job runs changed.
- **`scripts/verify.sh` still runs per commit in the gate**, and it is what keeps the eval cases
  running on every pull request now that `agent-evals` is nightly.
- **The control-plane block still holds.** `scripts/check_control_plane.sh` refuses an
  agent-authored diff to `PROTECTED_PATHS` until a human applies `control-plane-approved`. This work
  item's own PR-A was blocked by it and waited for the label.
- **The merge is still a human click** for supervised items
  (`knowledge/decisions/merge-click-is-the-gate.md`), and for delegated items
  `scripts/delegated_merge.py` still demands a `success` on every required workflow.
- **No test was skipped, removed or weakened.** `work/ci-budget/plan.md` R12 makes that a machine
  check: `git diff origin/main -- scripts/test_check_artifact_chain.py` is empty and the diff of
  `scripts/test_delegated_merge.py` carries no removed `def test_` line.

## Decision — loosened, and what compensates
- **A draft pull request gets no gate run and no review run** (the job `if:` in `sdlc-gate.yml` and
  `pr-review.yml`). Compensating: the agent runs `verify.sh` and the chain check locally at every
  step (`.claude/skills/sdlc-run/SKILL.md` step 4), GitHub refuses to merge a draft, and
  `delegated_merge.py` refuses one too. The build window is CI-free, not gate-free.
- **`agent-evals` no longer runs per pull request** (`on:` is `schedule` + `workflow_dispatch`).
  Compensating: the same cases run inside the gate's `verify.sh` step per commit, and `agent-evals`
  is never a required check — a workflow that never reports would otherwise block every merge.
- **The gate's failure triage runs only under the `triage` label.** Compensating: nothing about
  pass or fail changed — a red gate is still red, with its log. The label buys a judgment step, and
  that spend is the owner's decision; the agent asks and never applies it
  (`.claude/skills/sdlc-review/SKILL.md` step 4).
- **A Bot's `edited` on the pull-request body no longer starts the job.** Compensating: the job
  reads only the `Work-Item:` line, which no Bot writes; a human's `edited` still runs.
- **`_pr_runs` now ignores a `skipped` run, and a `cancelled` run where a later run of the same
  workflow succeeded.** Compensating: the join is on `workflow_id`, not the workflow *name* the head
  branch can write, and a run carrying no `workflow_id` supersedes nothing; `check_required_runs`
  still refuses when no `success` remains for a required workflow, so dropping can never turn
  "nothing passed" into "nothing failed". Both directions are pinned in
  `scripts/test_delegated_merge.py`.
- **The `delegation` condition ends a supervised item's merge run green** instead of red.
  Compensating: `pull-request` and `locked-paths` still evaluate and stay red, exit 0 is mapped only
  when `not-delegated` is the sole non-`ok` line, and an intent whose `status` is already
  `delegated` — an agent having signed its own grant — defers to the `grant` condition, which
  refuses it red.

## Consequences
- **GitHub counts a skipped required check as passing.** A Bot body edit on a ready pull request now
  produces a `skipped` gate run. Nothing merges on that alone today: `main` carries no
  branch-protection rule (spec C2), and the merge script refuses on the earlier red run. If the
  owner creates the rule, that is the fact to weigh — require `sdlc-gate / artifact-chain`, never
  `agent-evals`, and leave "require branches to be up to date" off.
- **A Linux-only failure surfaces one round later**, at the ready click rather than the first push.
- **The two widened paths in the merge script are the two places where a mistake could merge
  something that should not.** Both are bounded by named tests, and both landed in a pull request
  the owner read before labelling.
- **A stale tracking comment can sit on a draft** until the reviewer runs at ready. Harmless: it
  carries no verdict.
- **A red run on a sha is cleared by a push, never by a re-run.** `check_required_runs` keeps every
  failed run of a required workflow on the head sha, so a green re-run on the same sha — what the
  `triage` or `control-plane-approved` label triggers — leaves the merge script refusing. That is the
  spec's intent (R6 keeps `failure` and `timed_out` refusing), not a defect; it is written here
  because the label flow makes the same-sha re-run common, and `.claude/skills/sdlc-review/SKILL.md`
  step 4 says it where an agent will read it.
- **One residual is open, and it is fail-closed.** When a run is evicted from a concurrency group as
  `cancelled` and a later run of the same workflow succeeds on that sha, `_pr_runs` ignores the
  cancelled *workflow run* — but `check_check_runs` reads the commit's *check-run* rows, which have
  no supersession rule and do not accept `cancelled`. A live listing of PR #71's head sha returned
  two `artifact-chain` rows from two distinct runs, so the rows do persist per run rather than
  collapsing to the latest. The failure mode is a refusal, never a merge, and a push clears it.
  Closing it properly means keying a check-run supersession on `check_suite.id` — check-run rows
  carry no `workflow_id`, and a name join is what the security pass already ruled out — which is a
  new API surface and therefore the owner's spec decision, not a plan-level addition.
- **Regression is detectable, not hoped for.** `actions_minutes_per_pr` in
  `scripts/github_metrics.py` and its band in `monitoring/bands.yaml` make a return of the old spend
  a filed issue rather than a surprise on the billing page.

## Alternatives considered
- **GitHub Pro.** Roughly three more days of included minutes per month. A paid account decision the
  owner holds, and it treats a waste problem as a budget problem.
- **A spending limit.** Stops the work when it binds, rather than shaping what is spent.
- **Making the repository public** (free minutes). A disclosure decision the owner is taking
  separately; it also opens the `@claude` fork route, which is why `pr-review.yml` now resolves the
  head repository before any checkout.
- **A self-hosted runner.** An account and security decision, out of scope on the intent.

## Links
- `work/ci-budget/intent.md`, `spec.md`, `plan.md` — the numbers, the fourteen requirements, the file list
- `knowledge/decisions/merge-click-is-the-gate.md` — the click this record does not touch
- `knowledge/decisions/control-plane-label.md` — the label PR-A itself waited for
- `knowledge/decisions/delegated-mode.md` — the mode whose two acceptance paths were widened
