---
type: sdlc/work-item
id: ci-budget
title: Reduce GitHub minutes, waiting time and wasted tokens; keep the crucial procedures, loosen the rest
description: "The repository ran 1,124 workflow runs in six days on a private repo, exhausted the account's 2,000 free Actions minutes on 2026-09-08 21:43 UTC, and has been unable to run a single job since, including the owner's approval tap; most of those minutes, and the tokens and waiting behind them, went to work nobody used: superseded runs, a duplicate eval job, and a six-minute model triage of failures that were not the pull request's own."
timestamp: 2026-09-11T09:00:00Z
---
# Reduce GitHub minutes, waiting time and wasted tokens; keep the crucial procedures, loosen the rest

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; The repository ran 1,124 workflow runs in six days on a private repo, exhausted the account's 2,000 free Actions minutes on 2026-09-08 21:43 UTC, and has been unable to run a single job since, including the owner's approval tap; most of those minutes, and the tokens and waiting behind them, went to work nobody used: superseded runs, a duplicate eval job, and a six-minute model triage of failures that were not the pull request's own.
- [spec.md](spec.md) — status: in-review; approved-by: ; Two pull requests: the control plane (draft-skipping gate, label-gated triage, per-PR concurrency, nightly-only evals, two-workflow merge wake, the skipped-run rule and the not-delegated verdict in the merge script) and the agent side (draft-first skills, one code PR at a time, the actions_minutes_per_pr measure with its band, the crucial-versus-loosened decision record).

Last gate: - 2026-09-11T09:00:00Z | spec.md | (none) -> in-review | claude | ca8dd32 | fourteen requirement rows from the intent outcomes and implementation-plan.md, each with its test; four areas of concern (the two widened merge-script paths, no branch protection, the control-plane edit, the fork route); written on fable in the session that ran the mock walk, since the guide's opus writer was not this session's model, with a sonnet explorer re-checking every cited line against main (seven had moved); reviewers to run on opus and sonnet before the tap
