---
type: sdlc/work-item
id: ci-budget
title: Reduce GitHub minutes, waiting time and wasted tokens; keep the crucial procedures, loosen the rest
description: "The repository ran 1,124 workflow runs in six days on a private repo, exhausted the account's 2,000 free Actions minutes on 2026-09-08 21:43 UTC, and has been unable to run a single job since, including the owner's approval tap; most of those minutes, and the tokens and waiting behind them, went to work nobody used: superseded runs, a duplicate eval job, and a six-minute model triage of failures that were not the pull request's own."
timestamp: 2026-09-11T16:00:00Z
---
# Reduce GitHub minutes, waiting time and wasted tokens; keep the crucial procedures, loosen the rest

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; The repository ran 1,124 workflow runs in six days on a private repo, exhausted the account's 2,000 free Actions minutes on 2026-09-08 21:43 UTC, and has been unable to run a single job since, including the owner's approval tap; most of those minutes, and the tokens and waiting behind them, went to work nobody used: superseded runs, a duplicate eval job, and a six-minute model triage of failures that were not the pull request's own.
- [spec.md](spec.md) — status: approved; approved-by: luissiviero; Two pull requests: the control plane (draft-skipping gate, label-gated triage, per-PR concurrency, nightly-only evals, two-workflow merge wake, the skipped-run rule and the not-delegated verdict in the merge script) and the agent side (draft-first skills, one code PR at a time, the actions_minutes_per_pr measure with its band, the crucial-versus-loosened decision record).
- [plan.md](plan.md) — status: approved; approved-by: luissiviero; Two pull requests on one branch: the control plane (gate, review, evals and merge workflows plus the two merge-script rules) then the agent side (draft-first skills, the rule line, the actions_minutes_per_pr measure and its band, the decision record, the handoff).

Last gate: - 2026-09-13T17:05:00Z | PR #72 | draft -> in-review | claude | 29535f3 | PR-B ready for the owner after four review rounds: security sonnet, conformance sonnet, M4 revision fable, plus the automated reviewer once the gate runs. Nine findings changed the code. The diff touches no protected path, so no label is needed and the merge click is the only owner act. One decision is carried, not blocking: the C5 check-run residual is accepted and recorded in the decision record, or the owner amends the spec to key a check-run supersession on check_suite.id and re-taps. Writer opus, reviewers sonnet, revision fable
