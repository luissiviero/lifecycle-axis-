---
id: <slug>
stage: build
status: draft            # implementation hook refuses edits until 'approved'
reads: spec.md
approved-by:
approved-on:
risk-class: low          # low | medium | high (from intent.md)
---
# Plan: <title>

## Files
List every path that will change. Globs allowed. CI fails the PR if the diff touches anything else.
- src/example/module.ts — add X
- src/example/module.test.ts — tests for R1, R2

## Release-gated
Paths under RELEASE_GATED_PATHS with a named human owner (leave empty if none).
- migrations/0007_add_index.sql — owner: <name>

## Steps (in order, each independently verifiable)
1. 
2. 

## Verification
- Unit: `scripts/verify.sh`
- Acceptance: which spec rows are covered by which tests
- Manual / browser / eval:

## Risks and rollback
- Risk:  → mitigation:
- Rollback:

## Deviations log (append during implementation; same commit as the deviation)
- 
