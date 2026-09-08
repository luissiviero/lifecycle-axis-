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

Last gate: - 2026-09-08T15:05:00Z | plan.md | delegated -> delegated | claude | 120b92d | deviation: step 3 judges "retired" on the base ref, not the head; the pre-existing case InProgressChain.test_fully_superseded_chain_passes (batch-b-followups R-3) models the pull request that retires an item while the pointer still names it, which is the act in progress and must pass. The R-2 error fires when the base already has the intent superseded; the head's superseded intent earns a note to move the pointer in the same pull request. R-2's oracle unchanged; a fourth case pins the other side; no file added to the list. Also under risk 1: the two-line rules addition put the adopter's CLAUDE.md at 121 of 120, so the paragraph was re-flowed to net zero lines (prose only, every rule kept)
