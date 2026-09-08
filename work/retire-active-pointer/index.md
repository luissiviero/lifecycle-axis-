---
type: sdlc/work-item
id: retire-active-pointer
title: Retire `.sdlc/active` when a work item completes, so the plan gate stops opening on finished work
description: Nothing clears `.sdlc/active` when an item finishes, so it still names a merged item; require-plan.sh judges only that item's plan status and opens the code gate against a plan that has already landed.
timestamp: 2026-09-08T15:20:00Z
---
# Retire `.sdlc/active` when a work item completes, so the plan gate stops opening on finished work

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; Nothing clears `.sdlc/active` when an item finishes, so it still names a merged item; require-plan.sh judges only that item's plan status and opens the code gate against a plan that has already landed.
- [spec.md](spec.md) — status: delegated; approved-by: claude; Reuse `status: superseded` as the retirement mark the gate already closes on, make the chain check fail a pointer that names a retired item and note one that names another item, check the base ref it diffs against, and document the retirement act; the one-tap retire is a follow-up item.
- [plan.md](plan.md) — status: delegated; approved-by: claude; One test pins that a superseded plan closes the plan gate; check_artifact_chain.py gains the retired-pointer failure, the slug/pointer mismatch note and the base-ref check, each with a test; the rules fragment and the handoff carry the retirement act; no hook, workflow or skill is touched.

Last gate: - 2026-09-08T14:45:32Z | plan.md | in-review -> delegated | claude | 0697eb6 | twelve files and six steps from the signed spec; each of R-2, R-3, R-4 is written as a failing test first; no hook, workflow or skill in the list; the gh-absent crash on trailer verification is recorded as a risk with the documented author-rule fallback, not fixed here
