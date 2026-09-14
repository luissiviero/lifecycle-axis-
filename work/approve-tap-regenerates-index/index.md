---
type: sdlc/work-item
id: approve-tap-regenerates-index
title: The approval tap commits an approval whose indexes are stale; make the tap regenerate what it changes
description: The approve workflow runs the approval script and commits, but nothing in it runs gen_index.py, so every tap so far has left work/<slug>/index.md and work/index.md drifted on the ref it wrote to, and the committer's allowlist documents a regeneration that does not happen. This item makes the tap regenerate the indexes and commit them, and nothing else.
timestamp: 2026-09-14T02:45:00Z
---
# The approval tap commits an approval whose indexes are stale; make the tap regenerate what it changes

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; The approve workflow runs the approval script and commits, but nothing in it runs gen_index.py, so every tap so far has left work/<slug>/index.md and work/index.md drifted on the ref it wrote to, and the committer's allowlist documents a regeneration that does not happen. This item makes the tap regenerate the indexes and commit them, and nothing else.
- [spec.md](spec.md) — status: delegated; approved-by: claude; scripts/approve_dispatch.py --commit renders work/<slug>/index.md and work/index.md with gen_index.py's own renderer before it stages, commits every generated index it changed (other items' included, so a tap heals drift already on main), keeps refusing every other stray path, and its allowlist and docstring say so. The workflow, approve.py and the generator do not change.

Last gate: - 2026-09-14T02:43:57Z | spec.md | in-review -> delegated | claude | 864923e | designed from the owner's two answers in the intent: regeneration inside --commit via gen_index.render_all, every regenerated index committed, allowlist widened to the generated paths under six new committer cases; sign.py and the grant untouched
