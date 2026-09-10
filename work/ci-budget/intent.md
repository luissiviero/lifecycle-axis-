---
type: sdlc/intent
id: ci-budget
title: Reduce GitHub minutes, waiting time and wasted tokens; keep the crucial procedures, loosen the rest
description: "The repository ran 1,124 workflow runs in six days on a private repo, exhausted the account's 2,000 free Actions minutes on 2026-09-08 21:43 UTC, and has been unable to run a single job since, including the owner's approval tap; most of those minutes, and the tokens and waiting behind them, went to work nobody used: superseded runs, a duplicate eval job, and a six-minute model triage of failures that were not the pull request's own."
stage: plan
# status: draft | in-review | approved | delegated | superseded
status: approved
author: Luis Siviero (repo owner), in the session of 2026-09-09 that traced the Actions quota block; drafted by Claude from the owner's three goals and the run history of 1,124 workflow runs
# approved-by: product owner; set only by a human, with scripts/approve.py from their own shell
approved-by: luissiviero
approved-on: 2026-09-10
# risk-class: low | medium | high; the grant below is valid only for classes the policy lists
risk-class: low
# mode: supervised | delegated; delegated-by and delegated-on are set only by a human, like approved-by
mode: supervised
delegated-by:
delegated-on:
# supersedes: previous intent id, if any
supersedes:
# record: legacy system id (Jira/ServiceNow) if that system holds a copy
record:
resource: https://github.com/luissiviero/lifecycle-axis-/actions/runs/34288111993
tags: [ci, github-actions, minutes, tokens, latency, sdlc-gate, pr-review, agent-evals, delegated-merge, drafts, concurrency, branch-protection]
timestamp: 2026-09-09T09:10:00Z
---
# Intent: reduce GitHub minutes, waiting time and wasted tokens; keep the crucial procedures, loosen the rest

## Problem
In the owner's words, 2026-09-09:

> I've being receiving hundreds of emails like the one in the image

> if you check my last session you'll see something didn't go through because I reached some sort of
> GitHub limit

> make a plan on how you'd do it to reduce (a) GitHub minutes; (b) time; (c) unnecessarily spent tokens.
> for that, if we keep the crucial procedures, I don't mind loosen up the other ones to improve this 3
> items.

Measured on 2026-09-09 from the Actions API (the repository is private, created 2026-09-02; 1,124 runs
since; GitHub Free includes 2,000 Actions minutes a month for private repositories, billed per job and
rounded up to the minute):

- **The block.** The last run that executed is `sdlc-gate` #330, 2026-09-08 21:36:11 to 21:43:00 UTC.
  Every run since completes in 3 to 5 seconds with `failure` and no log archive (HTTP 404 on the job log:
  the job never reached a runner). Among them: the `approve` dispatch run 34288111993 at 22:53:34, the
  owner's `mode: delegated` tap for `approve-tap-regenerates-index`, dead after 3 seconds; and this
  morning's `agent-evals` and `bands` nightlies, dead after 4 and 5. That is the "something [that] didn't
  go through".
- **Where the minutes went** (the newest 100 runs of each workflow, billed with the one-minute floor,
  scaled to the totals): `sdlc-gate` 334 runs, about 770 minutes; `pr-review` 414 runs, about 650;
  `agent-evals` 166 runs, about 300; `delegated-merge` 185 runs, about 100; the two nightlies about 80.
  About 1,900 in six days, against a 2,000 allowance; about 30 billed minutes per pull request over 62.
- **The failure path is four times the success path.** A green `sdlc-gate` run is 0.8 minutes median
  (60 runs, 46 minutes in all). A red one is 3.6 median and 10.6 at worst (36 runs, 148 minutes), because
  on `failure()` the job installs `@anthropic-ai/claude-code` and runs `claude -p` with `Read,Grep,Glob`
  over the checkout. Run 34281512068 (pull request 61) shows the shape: `CHAIN: PASS`, 828 tests, 43 evals
  green, then `index-drift.sh` fails on `work/run-queue-followups/index.md`, a drift already on `main`
  from the approval commit c0aa58c (the subject of pull request 62), then `npm install` in 4 seconds and
  `claude -p` for **5 minutes 54 seconds**. Pull requests 59, 60 and 61 each paid the same, about 24
  minutes and four model runs to triage one known drift that was not theirs, and whose diagnosis the
  agent had already written into the pull request body.
- **Most runs were superseded before they mattered.** 89 of 96 `sdlc-gate` runs, 45 of 52 `pr-review`
  runs and 76 of 92 `agent-evals` runs on pull requests were followed by another push on the same branch.
  The gap to that next push is 5.3 minutes median; 33 of 89 gaps are under 3 minutes and 15 under 1,
  which is inside a 3-minute review or a 3.6-minute red gate. No workflow that runs on `pull_request` has
  a `concurrency:` group (`approve.yml`, `delegated-merge.yml` and `deploy.yml` do, all `cancel-in-progress:
  false`).
- **One job is a duplicate.** `agent-evals.yml`'s `hook-cases` job runs `scripts/run_evals.sh --kind hook`
  on every pull request whose diff touches `scripts/**`, `.claude/**`, `.sdlc/**` or `evals/**`, which is
  nearly every pull request here. `sdlc-gate` runs `scripts/verify.sh`, whose `VERIFY_CMDS`
  (`.sdlc/config.env`) already runs `scripts/run_evals.sh` on the same commit: the run above prints
  `EVALS: 43 pass, 0 fail, 6 skipped` inside the verify step. The 92 runs bought nothing the gate had not
  already proven, at a minute each; and `agent-evals` was removed from `merge.require-checks` on
  2026-09-06 (15424e0), yet `delegated-merge.yml` still lists it under `workflow_run.workflows`, so each of
  those runs also woke the merge script for a minute to print `waiting`.
- **The draft design exists; the practice and the gate do not follow it.** `.claude/skills/sdlc-review/SKILL.md`
  step 3 marks the pull request ready with `gh pr ready` and logs `PR #<n> | draft -> in-review`, and
  `pr-review.yml` already skips drafts (`github.event.pull_request.draft == false`). But the four open
  pull requests (59 to 62) are `draft: false` from the start, 38 of 55 pushes in the sample got a full
  review, and `sdlc-gate.yml` has no draft guard at all and no `ready_for_review` in its `types:` list, so
  a draft that went ready today would get no gate run until its next push.
- **The wait.** The checks run in parallel, so a push waits for the slowest: `pr-review` at 3.0 minutes
  median, or the red gate at 3.6. A green gate alone would be 0.8.
- **The inbox.** GitHub mails the actor on every failed run; about 40% of runs fail; that is the
  "hundreds of emails". (A week earlier, an invalid `sdlc-gate.yml` produced one failed run per push, with
  the file path as the workflow name; that was fixed on 2026-09-02 by dc7e4ba and is not this item.)

## Proposed outcome
- (a) **Minutes.** A pull request of pull request 61's shape (intent-only, four pushes) costs at most 6
  billed minutes end to end, against about 34 today (four pushes times gate, review, evals and the merge
  wake); the mean over the first week after the change is at most 10 billed minutes per pull request,
  against the 30 measured above. Observable: `scripts/github_metrics.py` gains a series that reads run
  durations per pull request from the Actions API, and `monitoring/bands.yaml` gains a band on it, so a
  regression is a filed issue, not a surprise on the billing page.
- (b) **Time.** A push to a draft waits for nothing. On a ready pull request, the wait from a push to a
  merge-eligible head is at most 4 minutes (gate under 1, review under 3), and a red gate is red inside
  1 minute instead of 3.6. Observable: `run_started_at` to `updated_at` on the runs after the change.
- (c) **Tokens.** No `claude -p` runs from CI on a failure unless the pull request carries a `triage`
  label; no review of a draft; at most one review per push after ready, the review of a superseded push
  cancelled. Observable: the `triage` step's `if:` in the Actions log; the count of `claude[bot]`
  tracking comments on a pull request is at most one plus the pushes after ready.
- **The crucial procedures are untouched, and say so in a decision record.** Kept: the artifact chain
  check, `scripts/verify.sh` and `scripts/check_control_plane.sh` on every ready head SHA before a merge;
  the check-run names `artifact-chain`, `review` and `merge` and the policy's `require-checks:
  [sdlc-gate, pr-review]` and `require-review: true` on the final SHA; human-only approvals and the
  approve tap; the nightly `agent-evals` full suite with `--require-claude` (the credential health check)
  and the nightly `bands`; the `@claude` on-demand review. Observable: `scripts/test_delegated_merge.py`
  (123 cases) and `scripts/test_check_artifact_chain.py` (78) pass unmodified; `knowledge/decisions/`
  gains a record listing what is crucial and what was loosened, so the next cost cut starts from it.
- Fewer failure emails in proportion to fewer runs; the owner's own notification setting is the other
  half and lives outside the repository.
- Everything ends green: `scripts/verify.sh` `VERIFY: PASS`, `check_artifact_chain.py` `CHAIN: PASS`,
  `scripts/run_evals.sh` `0 fail`, `scripts/check_okf.py` `0 warnings`; the adopter's rendered context
  file at or under `MAX_CONTEXT_LINES`.

## Affected users and systems
- Users: the owner (inbox, allowance, the tap that must go through); every agent session (the wait per
  push, the tokens per review); adopters of the kit (the workflow templates and the rule fragments).
- Services / repos / data: `.github/workflows/sdlc-gate.yml` (draft guard, `ready_for_review`,
  concurrency, label-gated triage), `pr-review.yml` (concurrency), `agent-evals.yml` (drop the
  `pull_request` trigger and `hook-cases`), `delegated-merge.yml` (`workflows: [sdlc-gate, pr-review]`),
  all under `PROTECTED_PATHS`; `.claude/skills/sdlc-intent`, `sdlc-run` and `sdlc-review` (open as draft,
  ready once at the end, one agent pull request open at a time); `docs/sdlc/rules/30-conventions.md` and the
  three regenerated context files; `docs/sdlc/github-setup.md` (required checks without `agent-evals`; the
  up-to-date rule as the owner decides); `scripts/github_metrics.py`, its test and `monitoring/bands.yaml`
  (the measure; `scripts/` is in `PLAN_REQUIRED_PATHS`); branch protection on `main` (owner's clicks);
  `knowledge/decisions/` (the crucial-versus-loosened record).

## Constraints
- Must: keep every procedure the "crucial" list above names, byte-for-byte where it is code and
  name-for-name where it is a check run; no job or workflow is renamed.
- Must: nothing merges from the draft window. The merge script and branch protection both require a
  green gate on the head SHA, and GitHub refuses to merge a draft; the draft window is CI-free, not
  gate-free.
- Must: the workflow diff ships in one control-plane pull request the owner labels `control-plane-approved`
  (knowledge/lessons/control-plane-unlock-is-advisory.md), and the branch-protection edit that drops
  `agent-evals` from the required checks lands in the same sitting, before the first ready pull request
  after it: a required check that no longer reports blocks every pull request forever.
- Must: land before the four open pull requests resume, not after; they need no close or reopen, since a
  `pull_request` run reads the workflow from the merge commit and picks the change up on the next push,
  and `workflow_run`, `schedule`, `issue_comment` and `workflow_dispatch` read `main` at once.
- Must: the fix cannot pass CI while CI is blocked; the owner unblocks Actions first (spending limit,
  reset date, or visibility, their call and out of scope here) or admin-merges with a ledger line.
  Done 2026-09-09: the owner made the repository public and changed nothing else; the gate ran green on
  this pull request's head at 12:36 UTC, in 32 seconds.
- Must not: skip, disable or quarantine a test or an eval to get green; touch approvals, grants,
  signatures, the merge method or the merge conditions; remove the nightly credential check; edit
  `.sdlc/`, `.claude/hooks/`, `scripts/verify.sh` or `scripts/checks/`.
- Out of scope: repository visibility, the spending limit and the GitHub plan (the owner's account
  decision, recorded as a companion decision if taken); making `index-drift.sh` tolerant of drift already
  on `main` (pull request 62); the owner's e-mail notification settings; the on-demand `@claude` route;
  self-hosted runners.

## Risk class
low — no merge condition changes; every edit removes a repetition, a duplicate, or adds a guard on a
draft, and each is a one-line revert. The failure mode of getting it wrong is a check that does not run
when it should, and two independent controls catch that before a merge: the merge script's
`require-checks` (a head SHA with no successful `sdlc-gate` run never merges) and the required status
check in branch protection. The same value is in the `risk-class` key above. The item is supervised
regardless: its diff touches `.github/workflows/`, which the policy's floor and `PROTECTED_PATHS` keep
out of any delegated merge.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: on a draft, does `sdlc-gate` skip entirely (no CI until ready), or run without the review? Proposed:
  skip; the agent runs `scripts/verify.sh` and the chain check locally at step 4 of `sdlc-run` anyway, and
  nothing merges from a draft. The trade is a Linux signal that arrives one round later: pull request 61's
  body records seven suites red on the owner's Windows PC and green on the runner, and the ready gate
  would catch the reverse case on its first run.
  A: skip entirely (owner, 2026-09-09).
- Q: the failure triage, removed or kept behind a `triage` label? Proposed: label; `labeled` is already a
  trigger type, so applying the label re-runs the gate with triage on, and the route costs nothing idle.
  A: label (owner, 2026-09-09).
- Q: "Require branches to be up to date" in branch protection: off, with "one agent pull request open
  at a time" as the compensating control, or on, accepting a forced merge-of-`main` round on every other
  open pull request per merge (the `work/index.md` conflict on pull request 62)? Proposed: off; the
  `sdlc-run` queue is serial by construction and the merge script re-checks every condition on the head
  it merges.
  A: off, with "one agent code pull request open at a time; intent-only ones may run beside it" as the
  compensating control (owner, 2026-09-09, accepting the proposal: under the queue a code pull request is
  branched from the fresh `main` after each merge, so the rule was redundant for code and only bit the
  parallel intent pull requests).
- Q: the review's model. The convention wants the reviewer on a different model from the writer, not a
  larger one; pinning a smaller model on `pr-review` would cut tokens per review. Proposed: not in this
  item; measure first (the tracking-comment count and the Actions durations are the proxies) and decide
  in the spec with a number.
  A: unchanged; the review verdict gates delegated merges (`require-review: true`), so cut the count first,
  measure a week, decide with a number (owner, 2026-09-09).
- Q: cancelling a superseded `pr-review` leaves that run's `claude[bot]` tracking comment saying it is
  working. Acceptable as is, or should the spec make the merge script and the skills read only the latest
  comment? Proposed: the spec checks which comment `scripts/delegated_merge.py` reads for `require-review`
  and changes nothing if it is already the latest.
  A: checked on 2026-09-09: `check_review` takes the newest completed `pr-review` run's id and reads only
  the comment linking that run (`scripts/delegated_merge.py:605-610`), so a cancelled run's comment is
  never read. No change.
- Q: the measure: a new series in `scripts/github_metrics.py` with a band (a `scripts/` change under this
  plan), or a number read by hand from the billing page each week? Proposed: the series; the Maintain
  play says a band, and the billing page has no history.
  A: the series, named `actions_minutes_per_pr` (owner, 2026-09-09).
- Q: (added after exploration) `scripts/delegated_merge.py` refuses a merge when any completed run of a
  required workflow on the head sha is not `success`, `skipped` and `cancelled` included
  (`check_required_runs` :339-364, `check_review` :581-628). A draft's last push and its ready run share
  a sha, so the draft-time `skipped` run would refuse every pull request that was ever a draft; a same-sha
  re-trigger that cancels a run in flight does the same. Proposed: a superseded-run rule — a `skipped` or
  `cancelled` run is ignored only when a later run (higher id) of the same workflow on the same sha
  concluded `success`; everything else refuses as today. This touches a locked-path script and refines the
  "no merge condition changes" constraint above; it ships in the control-plane pull request under the
  owner's click, with regression tests.
  A: approved (owner, 2026-09-09).
- Q: (added after exploration) how does Actions get unblocked, how many pull requests, which models, who
  writes the workflow diff? Proposed: the owner's call on the first; two pull requests (control plane
  first); Sonnet session writes, Opus subagents review, Fable checks the result against this intent;
  the agent writes under the unlock and the owner labels.
  A: make the repository public, after a fork-pull-request pass over the workflows and a history scan for
  secrets; two pull requests, control plane first; Sonnet writes, Opus reviews, Fable checks divergence
  from the objective; the agent writes under the unlock, the owner labels (owner, 2026-09-09). The full
  implementation guide is `work/ci-budget/implementation-plan.md`.
  Revised (owner, 2026-09-09, second session): the repository went public first, with no other change, so
  the fork-pull-request pass is the first item of the control-plane pull request rather than a
  precondition, and the settings the flip skipped are Phase 0 clicks; the session model is Opus, which
  writes and calls Sonnet subagents to scout, verify and review; Fable does a full revision at each
  milestone (spec and plan before the taps, each pull request's diff before it goes ready, the
  control-plane pull request merged with branch protection edited, the acceptance numbers before
  retirement), not only the divergence check. The history scan ran read-only in that session: nothing.
- Q: (second session, 2026-09-09) the superseded-run rule as first written compared run ids and covered
  `cancelled` too. A `skipped` run of a `pull_request` workflow can only come from a false job condition,
  which after this item means "the head was a draft", so it is never evidence of anything; and with
  cancel-in-progress bound to `synchronize`, a `cancelled` run never lands on the head sha. Proposed: drop
  `skipped` runs inside `_pr_runs` (one clause fixes the checks, review and cool-off conditions together)
  and keep refusing `cancelled` as today.
  A: the simpler rule (owner, 2026-09-09).
- Q: (second session) the gate's `edited` trigger. The last commit on this pull request got two full gate
  runs on the same sha, one from the push and one from Sourcery editing the body to append its summary,
  and each completion woke the merge script. Proposed: keep `edited` (a human fixing the `Work-Item:` line
  still gets a run) and skip the job when the event is `edited` and the sender is a Bot.
  A: keep with the Bot guard; Sourcery uninstalled as well (owner, 2026-09-09).
- Q: (second session) `scripts/delegated_merge.py` exits 1 on every refusal, so every gate or review
  completion on a supervised pull request is a red, billed `delegated-merge` run (run 34352116586:
  `CONDITION pull-request: refused — pull request #63 is a draft`). The draft case disappears with the
  draft guard; the supervised case stays. Proposed: a condition of its own, `delegation`, printed after
  `event`: when the base checkout's `work/<slug>/intent.md` for the body's `Work-Item` exists and its mode
  is not `delegated`, the verdict is `not-delegated` and the run exits 0; every other refusal stays red.
  This refines the "no merge condition changes" constraint the same way the skipped-run rule does. The
  owner has turned failure e-mails off, so the gain is the billed minute and a run list where red means
  "a human is needed".
  A: approved (owner, 2026-09-09).
- Q: (second session) the measure's filter. `head_branch != main` drops every `delegated-merge` wake: the
  live API shows `workflow_run` runs carrying `head_branch: main`. Proposed: sum the billed minutes of every
  run whose `event` is neither `schedule` nor `workflow_dispatch`, and divide by the distinct non-default
  head branches in the bucket.
  A: approved (owner, 2026-09-09).
- Q: (second session) `.sdlc/active` still names `run-queue-followups`, whose pull request merged but whose
  artifacts are not `superseded`; the plan gate reads that pointer, so the control-plane pull request
  cannot edit `scripts/` until it moves. Only a human writes `superseded` or the pointer. Proposed: the
  owner retires the item and points the file at `ci-budget` on `main`, before the control-plane pull
  request.
  A: the owner's step 0.0 (owner, 2026-09-09).
- Q: (second session) GitHub counts a `skipped` required check as passing. Nothing merges from a draft and
  the merge script demands `success`, so the plan's controls hold; the decision record should say so.
  A: say so in `knowledge/decisions/ci-budget-crucial-and-loosened.md` (owner, 2026-09-09).
- Q: (second session) the `triage` label does not exist yet (`control-plane-approved` does). Proposed: the
  owner creates it before the control-plane pull request goes ready.
  A: yes (owner, 2026-09-09; https://github.com/luissiviero/lifecycle-axis-/labels).
