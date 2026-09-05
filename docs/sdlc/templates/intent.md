---
type: sdlc/intent
id: <slug>
title: <one-line problem statement in the originator's words>
description: <one sentence for indexes and catalogs>
stage: plan
# status: draft | in-review | approved | delegated | superseded
status: draft
author: <originator name and team>
# approved-by: product owner; set only by a human, with scripts/approve.py from their own shell
approved-by:
approved-on:
# risk-class: low | medium | high; the grant below is valid only for classes the policy lists
risk-class: low
# mode: supervised | delegated; delegated-by and delegated-on are set only by a human, like approved-by
mode: supervised
delegated-by:
delegated-on:
# supersedes: previous intent id, if any
supersedes:
# record: legacy system id (Jira/ServiceNow) if that system holds a copy
record:
resource: <link to issue / incident / channel thread / band breach log>
tags: []
timestamp: 2026-09-04T22:38:45Z
---
# Intent: <title>

## Problem
What cannot be done today, who is affected, how we know. In the originator's words.

## Proposed outcome
What better looks like, observable. Add a number or a test where possible.

## Affected users and systems
- Users:
- Services / repos / data:

## Constraints
- Must:
- Must not:
- Out of scope:

## Risk class
low | medium | high — and why (blast radius, data sensitivity, regulation). Sets who approves spec and
plan, and which classes a delegation grant may use; the same value also goes in the `risk-class`
front-matter key above.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q:
  A:
