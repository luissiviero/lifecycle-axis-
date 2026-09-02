---
type: sdlc/rule-fragment
title: Workflow and conventions
description: Model-neutral stage order plus branch, commit and test conventions.
targets: [claude, gemini, agents]
order: 30
tags: [rules, conventions, workflow]
timestamp: 2026-09-02T00:00:00Z
---
## Workflow
One stage at a time: write `intent.md`, then `spec.md`, then `plan.md`, then implement,
then review, and file `incident.md` when something breaks. Templates for each artifact
are in `docs/sdlc/templates/`. Do not start an artifact until a human has approved the
previous one.

## Conventions
- Branch: `work/<slug>`. PR title starts with `[<slug>]`. PR body has `Work-Item: <slug>`.
- Commit messages explain *why*; reference the work item slug.
- Tests live next to the code they test; every bug fix adds a regression test.
