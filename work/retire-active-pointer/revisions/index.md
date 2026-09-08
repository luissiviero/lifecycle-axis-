---
type: index
title: Revisions for retire-active-pointer
description: Consensus records for re-signing an artifact of this work item, one file per revision, numbered in order.
tags: [okf, index, revisions, retire-active-pointer]
timestamp: 2026-09-08T18:20:00Z
---

# Revisions for retire-active-pointer

One file per revision, `revisions/<n>.md`, written when an already-signed artifact must be re-signed.
`.sdlc/delegation.yaml` sets `revisions: consensus` and `min-reviewers: 2`, so each record carries the
trigger with evidence, the proposal, and one `## Reviewer: <role> (<model>)` section per reviewer,
each ending `verdict: revise`. `scripts/sign.py --revision` refuses to write without one.

- [1.md](1.md) — `spec.md` after the round-1 review on pull request 53: R-2 narrowed to judge the base
  ref, and R-7 added for the pointer's boundary validation.
