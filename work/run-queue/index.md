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

Last gate: - 2026-09-08T17:25:01Z | spec.md | delegated -> delegated | claude | b144c55 | revision 1: R-3's ledger actor and the Interfaces shape corrected to github-actions[bot], the identity that makes the commit; the failure-modes paragraph now credits the non-forced push rather than a pointer re-read that cannot fire through run(); the oracle asserts the literal string instead of the code's own constant
