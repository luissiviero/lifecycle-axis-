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

Last gate: - 2026-09-14T03:49:06Z | PR #84 | draft -> in-review | claude | a5aca92 | follow-up to #83, merged delegated as ae69ebc at 03:45:28Z while this fix was being made: the automated review left one nit, the line-oriented porcelain parse split a rename on the first arrow; changed_paths now reads git status --porcelain -z, the reviewer repro pinned as an assertion and seen red first. VERIFY: PASS (a5aca92), CHAIN: PASS, EVALS: 46 pass 0 fail. The pointer still names this item after the merge: the advance did not land, as advance-push predicts
