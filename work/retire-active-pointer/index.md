---
type: sdlc/work-item
id: retire-active-pointer
title: Retire `.sdlc/active` when a work item completes, so the plan gate stops opening on finished work
description: Nothing clears `.sdlc/active` when an item finishes, so it still names a merged item; require-plan.sh judges only that item's plan status and opens the code gate against a plan that has already landed.
timestamp: 2026-09-07T12:00:00Z
---
# Retire `.sdlc/active` when a work item completes, so the plan gate stops opening on finished work

- [intent.md](intent.md) — status: in-review; approved-by: ; Nothing clears `.sdlc/active` when an item finishes, so it still names a merged item; require-plan.sh judges only that item's plan status and opens the code gate against a plan that has already landed.

Last gate: - 2026-09-07T12:00:00Z | intent.md | (none) -> in-review | claude | e520f45 | drafted from the follow-up recorded in work/delegated-mode/spec.md:226, work/approve-by-dispatch/intent.md:104 and spec.md:251, plus the gate state measured in this session; three questions answered as proposals for the owner to edit or accept
