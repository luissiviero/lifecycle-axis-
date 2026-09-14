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

Last gate: - 2026-09-14T03:05:00Z | plan.md | delegated -> delegated | claude | f8b0e1d | deviation: the build commit 98daa7c corrected the signed spec's design step 4 (the index-only refusal stages nothing, as R-5's acceptance test requires) and the deviation entry written beside it said the spec did not change; logged now as the plan pass asked. 2 of 5
