---
type: sdlc/work-item
id: approve-tap-regenerates-index
title: The approval tap commits an approval whose indexes are stale; make the tap regenerate what it changes
description: The approve workflow runs the approval script and commits, but nothing in it runs gen_index.py, so every tap so far has left work/<slug>/index.md and work/index.md drifted on the ref it wrote to, and the committer's allowlist documents a regeneration that does not happen. This item makes the tap regenerate the indexes and commit them, and nothing else.
timestamp: 2026-09-14T03:20:00Z
---
# The approval tap commits an approval whose indexes are stale; make the tap regenerate what it changes

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; The approve workflow runs the approval script and commits, but nothing in it runs gen_index.py, so every tap so far has left work/<slug>/index.md and work/index.md drifted on the ref it wrote to, and the committer's allowlist documents a regeneration that does not happen. This item makes the tap regenerate the indexes and commit them, and nothing else.
- [spec.md](spec.md) — status: delegated; approved-by: claude; scripts/approve_dispatch.py --commit renders work/<slug>/index.md and work/index.md with gen_index.py's own renderer before it stages, and on the default branch also every other item's index it finds stale, so a tap on main heals drift; on any other ref it writes and stages only the item's own two, because the chain check counts only those as the item's files. It keeps refusing every other stray path, judges a rename at both ends, and its allowlist and docstring say so. The workflow, approve.py and the generator do not change.
- [plan.md](plan.md) — status: delegated; approved-by: claude; scripts/approve_dispatch.py --commit decides its route from runner-set values, renders every index with gen_index.render_all, writes and allows other items' indexes only on the default branch, stages what one git status run reported, refuses an index-only diff before staging, judges a rename's source, and says so in its text; thirteen new cases in scripts/test_approve_dispatch.py, ten seen red before the code.

Last gate: - 2026-09-14T03:17:10Z | plan.md | delegated -> delegated | claude | 69c460f | revision 1: the heal of other items' indexes is scoped to the default branch because the chain check counts only the item's own files and a foreign index in a work branch's diff turns its pull request red; the route is read from runner-set values and fails narrow; a rename is judged at both ends; one status run feeds guard and staging. Two reviewers on Opus against a Fable writer, verdict revise each
