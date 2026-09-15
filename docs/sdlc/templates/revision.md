---
type: sdlc/revision
id: <slug>-revision-<n>
title: <title>
description: <one sentence>
artifact: plan.md
# kind: revision | detour  (detour: the trigger is a DETOUR needed line from scripts/check_detour.py and the proposal is a route that stays low; scripts/sign.py and the chain check read both kinds the same way)
kind: revision
trigger: "<the error or finding that blocks the plan, with evidence: command, output, file:line; for a detour, the DETOUR: needed line and every path it named>"
timestamp: 2026-09-04T22:38:45Z
---
# Revision <n>: <title>

## Proposal
What changes in `<artifact>`, and why this is the smallest change that clears the trigger. Quote the
trigger's evidence again here if it is not already committed elsewhere. For a detour: what the artifact
says once the route below is adopted, and what it stops saying.

## Route (detour only)
The low-only route the reviewers judge; delete this section on a `kind: revision` record.
- Outcome reached: which of the intent's outcomes the route reaches, and which it does not.
- Paths and their lists: every path the route touches and the list each falls under, as
  `scripts/check_detour.py` prints them; none may be locked.
- Why the class is honestly low: what the route changes and what it leaves untouched.
- Remainder for a human: the non-low work left over, its class, and the `work/<slug>-supervised` intent
  that will carry it.
- What goes stale: every place in spec.md and plan.md the route makes wrong, each named.

## Reviewer: <role> (<model>)
Assess, independently of the proposal's own reasoning: does the trigger actually block the plan as
written, or does the plan already cover it; is the proposed change the smallest one that clears the
trigger, or does it change more than the trigger requires; what else in the plan (files, order,
risks, proof) breaks or goes stale if this change lands. For a detour, judge the route instead: does it
reach the outcome it claims, is every path it touches honestly low, is the remainder named and classed,
and is everything it makes stale listed. State the reasoning, then end with:
verdict: revise

## Reviewer: <role> (<model>)
Same questions, from a different model than the writer and, where possible, than the other
reviewer (a second Claude model when no other is on the machine). State the reasoning, then end with:
verdict: revise

## Closing note
`scripts/sign.py --revision` re-signs the artifact only when every `## Reviewer:` section above ends
`verdict: revise` and there are at least as many sections as the policy's `min-reviewers`. A `keep`
verdict, on any reviewer, or too few sections, means the agent does not re-sign: it stops here and
calls the owner back instead of proceeding on a split or insufficient review. On a detour record a
split closes the record; a changed route is a new record, and the second closed record at one gate
parks the item (`.claude/skills/sdlc-run/SKILL.md`, "The detour rule").
