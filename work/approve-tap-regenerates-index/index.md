---
type: sdlc/work-item
id: approve-tap-regenerates-index
title: The approval tap commits an approval whose indexes are stale; make the tap regenerate what it changes
description: The approve workflow runs the approval script and commits, but nothing in it runs gen_index.py, so every tap so far has left work/<slug>/index.md and work/index.md drifted on the ref it wrote to, and the committer's allowlist documents a regeneration that does not happen. This item makes the tap regenerate the indexes and commit them, and nothing else.
timestamp: 2026-09-14T03:00:00Z
---
# The approval tap commits an approval whose indexes are stale; make the tap regenerate what it changes

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; The approve workflow runs the approval script and commits, but nothing in it runs gen_index.py, so every tap so far has left work/<slug>/index.md and work/index.md drifted on the ref it wrote to, and the committer's allowlist documents a regeneration that does not happen. This item makes the tap regenerate the indexes and commit them, and nothing else.
- [spec.md](spec.md) — status: delegated; approved-by: claude; scripts/approve_dispatch.py --commit renders work/<slug>/index.md and work/index.md with gen_index.py's own renderer before it stages, commits every generated index it changed (other items' included, so a tap heals drift already on main), keeps refusing every other stray path, and its allowlist and docstring say so. The workflow, approve.py and the generator do not change.
- [plan.md](plan.md) — status: delegated; approved-by: claude; scripts/approve_dispatch.py --commit renders every index with gen_index.render_all before it judges the tree, allows work/index.md and work/<dir>/index.md, stages what git status reports, refuses an index-only diff, and says so in its text; six new cases in scripts/test_approve_dispatch.py, three seen red before the change.

Last gate: - 2026-09-14T02:46:42Z | plan.md | in-review -> delegated | claude | e5ec667 | two code files and the item's own artifacts; six new committer cases, three to be seen red before the code; kind feature so the existing test file stays editable
