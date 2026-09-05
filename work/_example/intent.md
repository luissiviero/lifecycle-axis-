---
type: sdlc/intent
id: _example
title: Example work item
description: Always-green example so hooks and CI can be exercised end to end.
stage: plan
status: approved
author: repo maintainer
approved-by: luissiviero
approved-on: 2026-09-02
# risk-class: low | medium | high; the grant below is valid only for classes the policy lists
risk-class: low
# mode: supervised | delegated; delegated-by and delegated-on are set only by a human, like approved-by
mode: supervised
delegated-by:
delegated-on:
supersedes:
record:
resource: docs/sdlc/README.md
tags: [example]
timestamp: 2026-09-02T14:18:00Z
---
# Intent: keep an always-green example so hooks and CI can be exercised

## Problem
New contributors need a work item that already passes every gate, to see the loop run end to end.

## Proposed outcome
- `scripts/check_artifact_chain.py --slug _example` exits 0 on a clean branch

## Affected users and systems
- Users: contributors
- Services / repos / data: this repo only

## Constraints
- Must: keep every field and heading the templates in `docs/sdlc/templates/` have, in their order
- Must not: touch application code
- Out of scope: anything beyond documentation

## Risk class
low — documentation only.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: none
  A: none
