---
type: sdlc/work-item
id: ci-budget
title: Reduce GitHub minutes, waiting time and wasted tokens; keep the crucial procedures, loosen the rest
description: "The repository ran 1,124 workflow runs in six days on a private repo, exhausted the account's 2,000 free Actions minutes on 2026-09-08 21:43 UTC, and has been unable to run a single job since, including the owner's approval tap; most of those minutes, and the tokens and waiting behind them, went to work nobody used: superseded runs, a duplicate eval job, and a six-minute model triage of failures that were not the pull request's own."
timestamp: 2026-09-09T09:10:00Z
---
# Reduce GitHub minutes, waiting time and wasted tokens; keep the crucial procedures, loosen the rest

- [intent.md](intent.md) — status: in-review; approved-by: ; The repository ran 1,124 workflow runs in six days on a private repo, exhausted the account's 2,000 free Actions minutes on 2026-09-08 21:43 UTC, and has been unable to run a single job since, including the owner's approval tap; most of those minutes, and the tokens and waiting behind them, went to work nobody used: superseded runs, a duplicate eval job, and a six-minute model triage of failures that were not the pull request's own.

Last gate: - 2026-09-09T09:10:00Z | intent.md | (none) -> in-review | claude | 603695b | drafted from the owner's three goals (fewer GitHub minutes, less waiting, fewer wasted tokens; keep the crucial procedures, loosen the rest) and the Actions run history: the quota block at 2026-09-08 21:43 UTC after 1,124 runs, the approve tap that died in 3 seconds behind it, a 5m54s claude -p triage on every red gate (pull requests 59-61 each paid it for a drift already on main), the agent-evals PR job repeating what verify.sh ran, delegated-merge waking on a workflow the policy no longer requires, and 89 of 96 gate runs superseded by a later push; six questions answered as proposals for the owner to edit or accept
