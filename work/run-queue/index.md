---
type: sdlc/work-item
id: run-queue
title: Grant several items up front and let one delegated run work through them, so I can be away for hours
description: A delegated run ends at one ready pull request and nothing starts the next item; every grant tap repoints .sdlc/active at one item; so one tap buys one item and the project idles until the owner is back. Let the owner grant a queue of intents at the start and have the run advance from one merged item to the next granted one without a human.
timestamp: 2026-09-08T17:00:00Z
---
# Grant several items up front and let one delegated run work through them, so I can be away for hours

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; A delegated run ends at one ready pull request and nothing starts the next item; every grant tap repoints .sdlc/active at one item; so one tap buys one item and the project idles until the owner is back. Let the owner grant a queue of intents at the start and have the run advance from one merged item to the next granted one without a human.
- [spec.md](spec.md) — status: delegated; approved-by: claude; A deterministic next-item rule, an advance the merge workflow commits to main after it merges (the only place that may write .sdlc/active), ledger lines on both items, and a sdlc-run that loops on its own pull request's merge event instead of ending at one ready pull request.

Last gate: - 2026-09-08T16:54:10Z | spec.md | in-review -> delegated | claude | 3da8bb6 | six requirements from the delegated intent and an explorer pass; the advance is a write-back in delegated_merge.py after the merge, on main's checkout, because an item's own pull request may never contain .sdlc/active (ALWAYS_LOCKED) and the merge workflow already checks out main with contents write; next_item.py fixes a total order; the loop's wake is a skill instruction, flagged as C1; ten gotchas, three concerns
