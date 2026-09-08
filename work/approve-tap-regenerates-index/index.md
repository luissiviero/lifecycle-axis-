---
type: sdlc/work-item
id: approve-tap-regenerates-index
title: The approval tap commits an approval whose indexes are stale; make the tap regenerate what it changes
description: The approve workflow runs the approval script and commits, but nothing in it runs gen_index.py, so every tap so far has left work/<slug>/index.md and work/index.md drifted on the ref it wrote to, and the committer's allowlist documents a regeneration that does not happen. This item makes the tap regenerate the indexes and commit them, and nothing else.
timestamp: 2026-09-08T22:35:00Z
---
# The approval tap commits an approval whose indexes are stale; make the tap regenerate what it changes

- [intent.md](intent.md) — status: in-review; approved-by: ; The approve workflow runs the approval script and commits, but nothing in it runs gen_index.py, so every tap so far has left work/<slug>/index.md and work/index.md drifted on the ref it wrote to, and the committer's allowlist documents a regeneration that does not happen. This item makes the tap regenerate the indexes and commit them, and nothing else.

Last gate: - 2026-09-08T22:35:00Z | intent.md | in-review -> in-review | claude | 3ad6788 | the owner answered both questions, choosing a run that goes as long as possible without their input: the regeneration lives inside approve_dispatch.py --commit, not in the workflow, so the item touches no protected or locked path and a delegated run can carry it from grant to merge; and a tap commits every index it regenerates, other items' included, with the allowlist widened to work/*/index.md and work/index.md under its own test, so a tap heals drift on main instead of refusing on it or leaving it there. Affected systems, constraints and the risk class rewritten to match; nothing else in the intent changed
