---
type: sdlc/revision
id: <slug>-revision-<n>
title: <title>
description: <one sentence>
artifact: plan.md
trigger: "<the error or finding that blocks the plan, with evidence: command, output, file:line>"
timestamp: 2026-09-04T22:38:45Z
---
# Revision <n>: <title>

## Proposal
What changes in `<artifact>`, and why this is the smallest change that clears the trigger. Quote the
trigger's evidence again here if it is not already committed elsewhere.

## Reviewer: <role> (<model>)
Assess, independently of the proposal's own reasoning: does the trigger actually block the plan as
written, or does the plan already cover it; is the proposed change the smallest one that clears the
trigger, or does it change more than the trigger requires; what else in the plan (files, order,
risks, proof) breaks or goes stale if this change lands. State the reasoning, then end with:
verdict: revise

## Reviewer: <role> (<model>)
Same three questions, from a different model than the writer and, where possible, than the other
reviewer. State the reasoning, then end with:
verdict: revise

## Closing note
`scripts/sign.py --revision` re-signs the artifact only when every `## Reviewer:` section above ends
`verdict: revise` and there are at least as many sections as the policy's `min-reviewers`. A `keep`
verdict, on any reviewer, or too few sections, means the agent does not re-sign: it stops here and
calls the owner back instead of proceeding on a split or insufficient review.
