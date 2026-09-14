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

Last gate: - 2026-09-14T04:05:00Z | plan.md | delegated -> delegated | claude | 5b1aa0f | deviation: the automated review on #84 found rule 7 unmet, the rename-arrow misparse having been found twice; the lesson nul-terminated-git-output.md, its index entry and its pointer line are added, the hooks bullet in the CLAUDE-only fragment is re-flowed to pay for the line at the adopter's cap, and the context files are regenerated. CLAUDE.md in the diff makes #84 the owner's click. 5 of 5, the cap
