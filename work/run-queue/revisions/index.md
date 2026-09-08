---
type: index
title: Revisions for run-queue
description: Consensus records for re-signing an artifact of this work item, one file per revision, numbered in order.
tags: [okf, index, revisions, run-queue]
timestamp: 2026-09-08T19:00:00Z
---

# Revisions for run-queue

One file per revision, `revisions/<n>.md`, written when an already-signed artifact must be re-signed.
`.sdlc/delegation.yaml` sets `revisions: consensus` and `min-reviewers: 2`, so each record carries the
trigger with evidence, the proposal, and one `## Reviewer: <role> (<model>)` section per reviewer,
each ending `verdict: revise`. `scripts/sign.py --revision` refuses to write without one.

- [1.md](1.md) — `spec.md` after review round 1 on pull request 55: the ledger actor corrected to the
  bot that actually commits, and the push named as what makes a concurrent advance safe.
