---
type: sdlc/incident
id: <slug>-incident-<n>
title: <title>
description: <one sentence>
stage: maintain
status: draft
band-breached: <metric> @ <sigma>σ    # or: ticket / channel / scan finding
detected-on:
severity: sev1 | sev2 | sev3
owner:
resource: <alert, thread, or scan finding link>
tags: []
timestamp:
---
# Incident: <title>

## Timeline (UTC)
- 

## Impact
## Diagnosis (evidence: logs, metrics, commits)
## Action taken (PR through the review gate / pre-approved runbook / rollback)
## Eval added (path under evals/cases/ — mandatory before this record is closed)
## Lesson (one line; also appended to docs/sdlc/lessons.md)
## Follow-up intent
Link to the new `work/<slug>/intent.md` this incident opened, if the fix is larger than one PR.
