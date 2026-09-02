---
type: sdlc/plan
id: <slug>
title: <title>
description: <one sentence>
stage: build
status: draft            # implementation hook refuses code edits until 'approved'
kind: feature            # feature | fix   (fix ⇒ hook blocks edits to test files)
reads: spec.md
approved-by:             # engineer for routine; tech lead/architect for medium/high risk
approved-on:
risk-class: low
record:
resource:
tags: []
timestamp: 2026-09-02T20:00:00Z
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
