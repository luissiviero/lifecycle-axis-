---
type: sdlc/work-item
id: ci-budget
title: Reduce GitHub minutes, waiting time and wasted tokens; keep the crucial procedures, loosen the rest
description: "The repository ran 1,124 workflow runs in six days on a private repo, exhausted the account's 2,000 free Actions minutes on 2026-09-08 21:43 UTC, and has been unable to run a single job since, including the owner's approval tap; most of those minutes, and the tokens and waiting behind them, went to work nobody used: superseded runs, a duplicate eval job, and a six-minute model triage of failures that were not the pull request's own."
timestamp: 2026-09-10T08:17:42Z
---
# Reduce GitHub minutes, waiting time and wasted tokens; keep the crucial procedures, loosen the rest

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; The repository ran 1,124 workflow runs in six days on a private repo, exhausted the account's 2,000 free Actions minutes on 2026-09-08 21:43 UTC, and has been unable to run a single job since, including the owner's approval tap; most of those minutes, and the tokens and waiting behind them, went to work nobody used: superseded runs, a duplicate eval job, and a six-minute model triage of failures that were not the pull request's own.
- [spec.md](spec.md) — status: in-review; approved-by: ; Skip the gate on drafts and on a Bot's body edit, put one concurrency group on each pull-request workflow, gate the failure triage behind a label, drop the duplicate eval job and the merge wake behind it, teach the merge script that a skipped run is not evidence and that a supervised item is not its business, and measure the result as a banded series.

Last gate: - 2026-09-10T08:04:09Z | intent.md | in-review -> approved | luissiviero | 9811483
