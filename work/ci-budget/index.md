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
- [plan.md](plan.md) — status: in-review; approved-by: ; Two pull requests on one branch: the control plane (gate, review, evals and merge workflows plus the two merge-script rules) then the agent side (draft-first skills, the rule line, the actions_minutes_per_pr measure and its band, the decision record, the handoff).

Last gate: - 2026-09-11T16:00:00Z | plan.md | (none) -> in-review | claude | 4a8fb4f | thirty-four paths in the file list, thirteen steps, nine risks, every spec row mapped to its test. Two departures from implementation-plan.md, both recorded in the plan text for the owner to read at the tap: the two pull requests run sequentially on this session own branch reset from main between them, which is the one-code-pull-request-at-a-time control itself, rather than the two branch names the guide gives; and each milestone revision is a read-only fable subagent rather than a session model switch, which keeps one writer per item. Writer opus, reviewers sonnet, milestone revision fable
