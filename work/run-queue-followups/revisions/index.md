---
type: index
title: Revisions for run-queue-followups
description: Consensus records for re-signing an artifact of this work item, one file per revision, numbered in order.
tags: [okf, index, revisions, run-queue-followups]
timestamp: 2026-09-08T19:20:00Z
---

# Revisions for run-queue-followups

One file per revision, `revisions/<n>.md`, written when an already-signed artifact must be re-signed.
`.sdlc/delegation.yaml` sets `revisions: consensus` and `min-reviewers: 2`, so each record carries the
trigger with evidence, the proposal, and one `## Reviewer: <role> (<model>)` section per reviewer,
each ending `verdict: revise`. `scripts/sign.py --revision` refuses to write without one.

- [1.md](1.md) — `spec.md` before implementation: the guard asks which call site it is serving rather
  than which commit the base resolves to, because those are the same commit in the recorded scenario and
  the signed design was inert there; and a failed `git status` refuses instead of assuming a clean tree.
