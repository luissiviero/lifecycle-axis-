---
type: sdlc/work-item
id: approve-tap-regenerates-index
title: The approval tap commits an approval whose indexes are stale; make the tap regenerate what it changes
description: The approve workflow runs the approval script and commits, but nothing in it runs gen_index.py, so every tap so far has left work/<slug>/index.md and work/index.md drifted on the ref it wrote to, and the committer's allowlist documents a regeneration that does not happen. This item makes the tap regenerate the indexes and commit them, and nothing else.
timestamp: 2026-09-08T22:35:00Z
---
# The approval tap commits an approval whose indexes are stale; make the tap regenerate what it changes

- [intent.md](intent.md) — status: in-review; approved-by: ; The approve workflow runs the approval script and commits, but nothing in it runs gen_index.py, so every tap so far has left work/<slug>/index.md and work/index.md drifted on the ref it wrote to, and the committer's allowlist documents a regeneration that does not happen. This item makes the tap regenerate the indexes and commit them, and nothing else.

Last gate: - 2026-09-08T21:50:00Z | intent.md | (none) -> in-review | claude | d5da45f | drafted from the owner's report and the three tap commits on main (a903a91, 3da8bb6, c0aa58c), each of which committed the artifact, log.md and .sdlc/active and no index; gen_index.py --check on c0aa58c reports work/run-queue-followups/index.md and work/index.md drifted, and approve_dispatch.py's allowlist documents a regeneration nothing runs. Two questions for the owner, answered as proposals: where the regeneration lives, and what the tap does about drift it may not commit. This pull request cannot carry work/run-queue-followups/index.md without leaving in-progress mode, so that drift stays on main until that item's next commit or the owner regenerates
