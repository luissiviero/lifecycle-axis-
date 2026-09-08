---
type: sdlc/work-item
id: run-queue-followups
title: The chain check reports PASS on work it never saw; make it say so instead
description: "check_artifact_chain.py diffs <base>...HEAD, so staged and uncommitted work is invisible to it; an empty diff is in-progress mode, and the check prints CHAIN: PASS under a note describing a diff that does not exist. It audited the wrong work twice in one session. The lesson written for it says the guard is nowhere yet; this item writes the guard."
timestamp: 2026-09-08T18:40:00Z
---
# The chain check reports PASS on work it never saw; make it say so instead

- [intent.md](intent.md) — status: in-review; approved-by: ; check_artifact_chain.py diffs <base>...HEAD, so staged and uncommitted work is invisible to it; an empty diff is in-progress mode, and the check prints CHAIN: PASS under a note describing a diff that does not exist. It audited the wrong work twice in one session. The lesson written for it says the guard is nowhere yet; this item writes the guard.

Last gate: - 2026-09-08T18:40:00Z | intent.md | in-review -> in-review | claude | bc36009 | narrowed by the owner after pull request 57 merged, which shipped two of the three leftovers: the sdlc-run skill now prints the active slug then the rest excluding it, and both lessons are filed with their rule pointers. What is left is the only piece needing code, and the lesson written for it says so itself -- knowledge/lessons/commit-before-the-chain-check.md ends "Where it is enforced: Nowhere yet". Rebased onto a83c8e4; three open questions replaced with the ones the guard raises; the intent now flags that scripts/check_artifact_chain.py is on the policy's locked-paths, so this item's merge is the owner's click and it is granted last
