---
type: sdlc/work-item
id: advance-push
title: The post-merge advance never lands, because it pushes from a checkout older than the merge it follows
description: delegated_merge.py advances .sdlc/active by committing on the job's checkout of main, taken before the merge API call moved main; the push is non-fast-forward every time and is swallowed as a note, so no queue has ever advanced live. Fetch and fast-forward onto the merged main before writing, with a regression test whose remote moves.
timestamp: 2026-09-14T05:20:00Z
---
# The post-merge advance never lands, because it pushes from a checkout older than the merge it follows

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; delegated_merge.py advances .sdlc/active by committing on the job's checkout of main, taken before the merge API call moved main; the push is non-fast-forward every time and is swallowed as a note, so no queue has ever advanced live. Fetch and fast-forward onto the merged main before writing, with a regression test whose remote moves.
- [spec.md](spec.md) — status: in-review; approved-by: ; delegated_merge.advance() fetches the default branch, refuses unless the fetched tip is the merge commit the API returned, fast-forwards the job's checkout onto it, and only then writes and pushes, so the advance commit's parent is the merge commit and the push is a fast-forward; a rejected push after that stays a note. Proven by a fixture whose bare remote moves between the checkout and the advance, as the merge API moves main.

Last gate: - 2026-09-14T05:18:42Z | spec.md | (none) -> in-review | claude | 7513ff5 | drafted on the owner direction from the three answered questions: fetch the checkout branch, refuse unless the fetched tip is the merge commit the API returned, fast-forward, then the existing write and non-forced push; the merge sha threaded from run() through a new merge_sha keyword; six cases in a new module because the plan is kind: fix and the hook locks the existing test file, four to be seen red before the code; writer Fable, reviewers to run on Opus
