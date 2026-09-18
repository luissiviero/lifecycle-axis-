---
type: index
title: Revisions for chain-check-without-gh
description: Consensus records for signing an artifact of this work item around a locked path, one file per record, numbered in order.
tags: [okf, index, revisions, detour, chain-check-without-gh]
timestamp: 2026-09-18T17:10:00Z
---

# Revisions for chain-check-without-gh

One file per record, `revisions/<n>.md`. `.sdlc/delegation.yaml` sets `revisions: consensus` and
`min-reviewers: 2`, so each record carries the trigger with evidence, the proposal, and one
`## Reviewer: <role> (<model>)` section per reviewer, each ending `verdict: revise`. The records here are
`kind: detour`: the trigger is `scripts/check_detour.py` naming `scripts/check_artifact_chain.py` on the
policy's `locked-paths`, and the route is the detour rule's step 5, a ready pull request the owner merges
by click, parked from a ledger-only pull request.

- [1.md](1.md) — `spec.md`, the spec gate: the fix is the one locked file; build it to a ready pull request
  and park with `click needed`. plan-reviewer (claude-sonnet-5) and security-reviewer (claude-opus-5) both
  `revise`; two corrections taken into the record (where the plan states the click; the blast radius after
  the click is the gate on `main`, so the net there is the owner's reading, not CI).
