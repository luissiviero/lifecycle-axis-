---
type: sdlc/spec
id: _example
title: Example work item spec
description: Spec for the always-green example; no code, exists so the hooks have an approved plan to point at.
stage: design
status: approved
reads: intent.md
approved-by: luissiviero
approved-on: 2026-09-02
skills-applied: []
timestamp: 2026-09-02T14:18:00Z
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
