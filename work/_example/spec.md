---
id: _example
stage: design
status: approved
reads: intent.md
approved-by: luissiviero
approved-on: 2026-09-02
standards-applied: []
---
# Spec: example work item

## Requirements
| # | Requirement | Intent criterion | Acceptance test |
|---|---|---|---|
| R1 | Chain check passes | 1 | `python3 scripts/check_artifact_chain.py --slug _example` |

## Design
No code. Exists so the hooks have an approved plan to point at.

## Decisions
- D1: keep the example under `work/_example` so it is exempt from plan-conformance checks.

## Not doing
- anything else
