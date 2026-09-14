---
type: index
title: Revisions for approve-tap-regenerates-index
description: Consensus records for re-signing an artifact of this work item, one file per revision, numbered in order.
tags: [okf, index, revisions, approve-tap-regenerates-index]
timestamp: 2026-09-14T03:05:00Z
---

# Revisions for approve-tap-regenerates-index

One file per revision, `revisions/<n>.md`, written when an already-signed artifact must be re-signed.
`.sdlc/delegation.yaml` sets `revisions: consensus` and `min-reviewers: 2`, so each record carries the
trigger with evidence, the proposal, and one `## Reviewer: <role> (<model>)` section per reviewer,
each ending `verdict: revise`. `scripts/sign.py --revision` refuses to write without one.

- [1.md](1.md) — `spec.md` and `plan.md` after the first review round: a tap heals every index only on
  the default branch, because the chain check counts only the item's own files and a foreign index in a
  work branch's diff turns its pull request red; elsewhere it writes the item's own two indexes; and a
  rename is judged at both ends, not only its destination.
