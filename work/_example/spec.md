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
skills-version:
prompt: (none; written by hand)
record:
resource:
tags: [example]
timestamp: 2026-09-02T14:18:00Z
---
# Spec: example work item

## Requirements (each maps to an intent outcome)
| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R1 | Chain check passes | 1 | `python3 scripts/check_artifact_chain.py --slug _example` |

## Design
### Architecture / data flow
No code. Exists so the hooks have an approved plan to point at.
### Interfaces (APIs, events, schemas) — exact shapes
(none)
### Data and migrations
(none)
### Failure modes and how they surface
(none)

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- (none)

## Open questions carried from intent.md
- (none)

## Decisions (ADR-style: context → decision → consequences)
- D1: keep the example under `work/_example` so it is exempt from plan-conformance checks.

## Gotchas found while reading the codebase
- (none)

## Not doing
- anything else
