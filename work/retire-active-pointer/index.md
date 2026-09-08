---
type: sdlc/work-item
id: retire-active-pointer
title: Retire `.sdlc/active` when a work item completes, so the plan gate stops opening on finished work
description: Nothing clears `.sdlc/active` when an item finishes, so it still names a merged item; require-plan.sh judges only that item's plan status and opens the code gate against a plan that has already landed.
timestamp: 2026-09-08T15:00:00Z
---
# Retire `.sdlc/active` when a work item completes, so the plan gate stops opening on finished work

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; Nothing clears `.sdlc/active` when an item finishes, so it still names a merged item; require-plan.sh judges only that item's plan status and opens the code gate against a plan that has already landed.
- [spec.md](spec.md) — status: delegated; approved-by: claude; Reuse `status: superseded` as the retirement mark the gate already closes on, make the chain check fail a pointer that names a retired item and note one that names another item, check the base ref it diffs against, and document the retirement act; the one-tap retire is a follow-up item.

Last gate: - 2026-09-08T14:42:56Z | spec.md | in-review -> delegated | claude | a903a91 | six requirements with oracles from the delegated intent and an explorer pass; retired is the existing superseded status, the hook is untouched, the chain check gains the retired-pointer failure, the mismatch note and the base-ref check; the one-tap retire is a follow-up item; ten gotchas, three concerns
