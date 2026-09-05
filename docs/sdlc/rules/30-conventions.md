---
type: sdlc/rule-fragment
title: Workflow and conventions
description: Model-neutral stage order plus branch, commit and test conventions.
targets: [claude, gemini, agents]
order: 30
tags: [rules, conventions, workflow]
timestamp: 2026-09-04T22:38:45Z
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
- `work/<slug>/log.md` gets an entry at every gate (format in `docs/sdlc/templates/log.md`); `approved-by` must be a
  handle from `.sdlc/approvers.yaml`; decisions go to `knowledge/decisions/`; institutional knowledge goes to
  `knowledge/`, and CLAUDE.md/GEMINI.md link to it rather than restating it.
- Humans approve from their own shell with `python3 scripts/approve.py <slug> <artifact>` (once per clone:
  `git config sdlc.approver <github-handle>`, or pass `--as <handle>`; it enforces intent → spec → plan order), or by
  editing the artifact plus `log.md` in the GitHub web editor; then commit as themselves. The script refuses to run
  inside an agent session; an agent asks for approval and waits. CI checks the approval commit's author.
