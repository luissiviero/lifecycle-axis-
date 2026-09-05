---
type: sdlc/plan
id: _example
title: Example work item plan
description: Plan for the always-green example; touches docs and work/_example only.
stage: build
status: approved
kind: feature
reads: spec.md
approved-by: luissiviero
approved-on: 2026-09-02
risk-class: low
record:
resource:
tags: [example]
timestamp: 2026-09-02T14:18:00Z
---
# Plan: example work item (from intent.md 2026-09-02)

## Files that change
- docs/**
- work/_example/**

## Release-gated
(none)

## Order of work (each step independently verifiable)
1. Nothing to implement.

## Risks
- none

## Proof
- `python3 scripts/check_artifact_chain.py --slug _example`

## Rollback
- (none; documentation only)

## Deviations log (append during implementation; same commit as the deviation)
- 
