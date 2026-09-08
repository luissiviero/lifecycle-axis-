---
type: sdlc/work-item
id: advance-push
title: The post-merge advance never lands, because it pushes from a checkout older than the merge it follows
description: delegated_merge.py advances .sdlc/active by committing on the job's checkout of main, taken before the merge API call moved main; the push is non-fast-forward every time and is swallowed as a note, so no queue has ever advanced live. Fetch and fast-forward onto the merged main before writing, with a regression test whose remote moves.
timestamp: 2026-09-08T22:00:00Z
---
# The post-merge advance never lands, because it pushes from a checkout older than the merge it follows

- [intent.md](intent.md) — status: in-review; approved-by: ; delegated_merge.py advances .sdlc/active by committing on the job's checkout of main, taken before the merge API call moved main; the push is non-fast-forward every time and is swallowed as a note, so no queue has ever advanced live. Fetch and fast-forward onto the merged main before writing, with a regression test whose remote moves.

Last gate: - 2026-09-08T21:35:51Z | intent.md | in-review -> in-review | claude | cf8ce1c | open questions answered by the owner: every proposal accepted as written
