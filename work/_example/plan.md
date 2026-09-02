---
type: sdlc/plan
id: _example
title: Example work item plan
description: Plan for the always-green example; touches docs and work/_example only.
kind: feature
stage: build
status: in-review
reads: spec.md
approved-by: luissiviero
approved-on: 2026-09-02
risk-class: low
timestamp: 2026-09-02T14:18:00Z
---
# Plan: example work item

## Files that change
- docs/**
- work/_example/**

## Release-gated
(none)

## Order of work
1. Nothing to implement.

## Proof
- `python3 scripts/check_artifact_chain.py --slug _example`

## Risks
- none

## Deviations log
- 
