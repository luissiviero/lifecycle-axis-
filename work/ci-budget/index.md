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

Last gate: - 2026-09-11T16:45:00Z | plan.md | in-review -> in-review | claude | a484f63 | the automated reviewer on the ready pull request, Important 1 Nits 0, a memory-pass finding: six commands in this plan would have passed with the work absent, one shape caught six times, and rule 7 asks for a lesson in the same pull request. It cannot be this one: a knowledge or docs path in the diff leaves in-progress mode, and strict mode needs an approved plan, which is what this pull request is asking for. The lesson, its index line and the pointer fragment therefore join the file list and step 8, whose budget is now two rendered lines paid by re-flowing prose and measured on the adopter render. Answered on the pull request. Writer opus, reviewer claude bot on the ready head
