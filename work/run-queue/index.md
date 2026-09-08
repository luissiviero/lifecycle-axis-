---
type: sdlc/work-item
id: run-queue
title: Grant several items up front and let one delegated run work through them, so I can be away for hours
description: A delegated run ends at one ready pull request and nothing starts the next item; every grant tap repoints .sdlc/active at one item; so one tap buys one item and the project idles until the owner is back. Let the owner grant a queue of intents at the start and have the run advance from one merged item to the next granted one without a human.
timestamp: 2026-09-08T17:20:00Z
---
# Grant several items up front and let one delegated run work through them, so I can be away for hours

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; A delegated run ends at one ready pull request and nothing starts the next item; every grant tap repoints .sdlc/active at one item; so one tap buys one item and the project idles until the owner is back. Let the owner grant a queue of intents at the start and have the run advance from one merged item to the next granted one without a human.
- [spec.md](spec.md) — status: delegated; approved-by: claude; A deterministic next-item rule, an advance the merge workflow commits to main after it merges (the only place that may write .sdlc/active), ledger lines on both items, and a sdlc-run that loops on its own pull request's merge event instead of ending at one ready pull request.
- [plan.md](plan.md) — status: delegated; approved-by: claude; scripts/next_item.py fixes the queue order; delegated_merge.py advances .sdlc/active and both ledgers on main after a successful merge, behind a staged-path allowlist and a lost-update guard; the sdlc-run skill subscribes to its pull request and loops on the merge instead of ending.

Last gate: - 2026-09-08T19:10:00Z | PR #55 | draft -> in-review | claude | aec7bd4 | review posted: four Important and four nits from the security and plan-conformance passes, both on sonnet against an Opus 5 writer, all fixed with a regression case each; revision 1 re-signed spec.md under two revise verdicts. VERIFY: PASS (aec7bd4), CHAIN: PASS, EVALS: 43 pass 0 fail, OKF: 169 docs 0 warnings
