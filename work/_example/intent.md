---
type: sdlc/intent
id: _example
stage: plan
status: approved
originator: repo maintainer
approved-by: luissiviero
approved-on: 2026-09-02
source: docs/sdlc/README.md
---
# Intent: keep an always-green example so hooks and CI can be exercised

## Problem
New contributors need a work item that already passes every gate, to see the loop run end to end.

## Success criteria
- `scripts/check_artifact_chain.py --slug _example` exits 0 on a clean branch

## Affected users and systems
- Users: contributors
- Services / repos / data: this repo only

## Constraints and non-goals
- Must not: touch application code

## Risk class
low — documentation only.

## Open questions
- none
