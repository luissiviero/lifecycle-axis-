---
type: sdlc/work-item
id: advance-push
title: The post-merge advance never lands, because it pushes from a checkout older than the merge it follows
description: delegated_merge.py advances .sdlc/active by committing on the job's checkout of main, taken before the merge API call moved main; the push is non-fast-forward every time and is swallowed as a note, so no queue has ever advanced live. Fetch and fast-forward onto the merged main before writing, with a regression test whose remote moves.
timestamp: 2026-09-14T05:45:00Z
---
# The post-merge advance never lands, because it pushes from a checkout older than the merge it follows

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; delegated_merge.py advances .sdlc/active by committing on the job's checkout of main, taken before the merge API call moved main; the push is non-fast-forward every time and is swallowed as a note, so no queue has ever advanced live. Fetch and fast-forward onto the merged main before writing, with a regression test whose remote moves.
- [spec.md](spec.md) — status: approved; approved-by: luissiviero; delegated_merge.advance() fetches the default branch, refuses unless the fetched tip is the merge commit the API returned, fast-forwards the job's checkout onto it, and only then writes and pushes, so the advance commit's parent is the merge commit and the push is a fast-forward; a rejected push after that stays a note. Proven by a fixture whose bare remote moves between the checkout and the advance, as the merge API moves main.
- [plan.md](plan.md) — status: in-review; approved-by: ; delegated_merge.advance() gains a merge_sha keyword and three steps before its dirty check (fetch the checkout's branch, refuse unless the fetched tip is the merge commit, fast-forward with --ff-only), run() passes the merge endpoint's sha; six cases in the new scripts/test_delegated_merge_advance.py on a fixture whose bare remote moves after the checkout, five red before the code; one sentence in knowledge/decisions/run-queue.md.

Last gate: - 2026-09-14T05:42:13Z | plan.md | (none) -> in-review | claude | d7045b6 | kind fix, so the six regression cases go in a new module and no existing test file changes; three files of code and record (the merge script, the new module, one sentence in the run-queue decision) plus this item's own; five of six cases predicted red before the code where the spec says four, whichever count step 1 observes corrects the other document in the same commit
