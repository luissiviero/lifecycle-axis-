---
type: index
title: Revisions for retire-delegated-items
description: Consensus records for amending an approved artifact of this work item, one file per revision, numbered in order.
tags: [okf, index, revisions, retire-delegated-items]
timestamp: 2026-09-14T17:45:00Z
---

# Revisions for retire-delegated-items

One file per revision, `revisions/<n>.md`, written when an artifact that already carries a human's
approval must change in what it requires. `.sdlc/delegation.yaml` sets `revisions: consensus` and
`min-reviewers: 2`, so each record carries the trigger with evidence, the proposal, and one
`## Reviewer: <role> (<model>)` section per reviewer, each ending `verdict: revise`. This item is
supervised, so no `sign.py --revision` follows the record: the owner's acceptance is a ledger line in
their own hand.

- [1.md](1.md) — `spec.md` during plan step 2: R-1 and D1 narrowed so `approved-by` is skipped only
  where the ledger shows the artifact signed under a grant, because the pre-existing case pinning a
  human-approved plan with a bot approver went red and the intent keeps every existing case green.
