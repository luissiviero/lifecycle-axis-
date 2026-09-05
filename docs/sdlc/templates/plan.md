---
type: sdlc/plan
id: <slug>
title: <title>
description: <one sentence>
stage: build
# status: draft | in-review | approved | delegated | superseded  (require-plan.sh refuses code edits until approved)
status: draft
# kind: feature | fix  (fix: protect-tests.sh refuses edits to existing test files)
kind: feature
reads: spec.md
# approved-by: engineer for routine; tech lead/architect for medium/high risk; set only by a human
approved-by:
approved-on:
risk-class: low
record:
resource:
tags: []
timestamp: 2026-09-04T22:38:45Z
---
# Plan: <title> (from intent.md <date>)

## Files that change
Every path that will change. Globs allowed. CI fails the PR if the diff touches anything else.
- src/example/module.ts — add X
- src/example/module.test.ts — tests for R1, R2

## Release-gated
Paths under RELEASE_GATED_PATHS with a named human owner (leave "(none)" if none).
- migrations/0007_add_index.sql — owner: <name>

## Order of work (each step independently verifiable)
1. 
2. 

## Risks
- Risk:  → mitigation:
- What this could break:
- Options considered and not taken:

## Proof
- `scripts/verify.sh` green
- Spec rows → tests: R1 → test_x; R2 → test_y
- Manual / browser / screenshot / eval:

## Rollback
- 

## Deviations log (append during implementation; same commit as the deviation)
- 
