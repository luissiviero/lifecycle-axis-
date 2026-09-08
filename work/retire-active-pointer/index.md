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

Last gate: - 2026-09-08T15:18:00Z | plan.md | delegated -> delegated | claude | b91969d | deviation: review round 1 (security-reviewer and plan-reviewer on opus; writer Fable 5.1), three Important findings each fixed with a regression test: the self-check (--base HEAD) has no base, so a retired pointer there is a note and the failure is CI's; the pointer and --slug are validated with SLUG_RE before naming a path or a git argument (the lesson one-path-spelling-in-guards.md recurring, applied); the signed spec revised under revisions/1.md. Nits taken; three files added to the list: spec.md (missing from it), revisions/1.md, docs/sdlc/README.md. 2 of 5
