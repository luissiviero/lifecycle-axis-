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

Last gate: - 2026-09-08T19:40:00Z | plan.md | delegated -> delegated | claude | 44cac9d | deviation: the documentation audit before ending the session -- five statements this item made false corrected (the run description in both model fragments and the README, HANDOFF's no-write-back line, the skill's printed queue, which must start at the pointer so the last tap runs first) and two rule-7 lessons added (the adopter's context file at the cap, met on two consecutive items; commit before the chain check, met twice this session), paid for at the adopter's cap by deleting the blank-line pointer that CaseBlocksAreWhole now makes impossible and re-flowing the tap paragraph in 30-conventions.md (adopt.sh rewrites the chain header by exact literal, and a first attempt there broke it); adopter renders at 120, the cap, as before; no code changed
