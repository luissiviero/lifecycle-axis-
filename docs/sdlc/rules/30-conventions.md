---
type: sdlc/rule-fragment
title: Workflow and conventions
description: Model-neutral stage order plus branch, commit and test conventions.
targets: [claude, gemini, agents]
order: 30
tags: [rules, conventions, workflow]
timestamp: 2026-09-05T20:00:00Z
---
## Workflow
One stage at a time: write `intent.md`, then `spec.md`, then `plan.md`, then implement,
then review, and file `incident.md` when something breaks. Templates for each artifact
are in `docs/sdlc/templates/`. Do not start an artifact until a human has approved the
previous one, or the agent has signed it under a delegation grant.

## Conventions
- Branch: `work/<slug>` for a human; an agent session's branch carries a prefix from `AGENT_BRANCH_PREFIXES`
  (`claude/`). PR title starts with `[<slug>]`. PR body has `Work-Item: <slug>`.
- Commit messages explain *why*; reference the work item slug.
- Tests live next to the code they test; every bug fix adds a regression test.
- A review runs on a **different model from the one that wrote the work**, whenever a second one is available:
  a writer re-reading its own diff shares its own blind spots, and this repo has the scars to prove it (three
  review rounds on pull request 51, each finding real defects in the previous round's fixes, two of them
  introduced by the fix before). The item's ledger records which model wrote it and which reviewed it — the
  owner writes those names, as `revisions/<n>.md`'s `## Reviewer: <role> (<model>)` heading already expects —
  so a later reader can tell whether the second pair of eyes was genuinely a second pair.
- `work/<slug>/log.md` gets an entry at every gate (format in `docs/sdlc/templates/log.md`); `approved-by` must be a
  handle from `.sdlc/approvers.yaml`; decisions go to `knowledge/decisions/`; institutional knowledge goes to
  `knowledge/`, and CLAUDE.md/GEMINI.md link to it rather than restating it.
- Humans approve one of three ways; the tap is the cheapest. **Actions -> approve -> Run workflow**
  (`.github/workflows/approve.yml`) with `slug`, `artifact` and `mode` runs the approval script as the run's
  actor and commits the result with `Approved-Run`/`Approved-Actor` trailers that CI verifies against the run
  record. An agent asks for the tap by naming those three inputs, and waits.
- Humans approve from their own shell with `python3 scripts/approve.py <slug> <artifact>` (once per clone:
  `git config sdlc.approver <github-handle>`, or pass `--as <handle>`; it enforces intent → spec → plan order), or by
  editing the artifact plus `log.md` in the GitHub web editor; then commit as themselves. The script refuses to run
  inside an agent session; an agent asks for approval and waits. CI checks the approval commit's author.
- When the intent has `mode: delegated`, the agent signs with `python3 scripts/sign.py <slug> <artifact>` under
  its own handle; ledger lines read `-> delegated`, with `deviation:` and `revision <n>:` notes as the case may
  be; re-signing an already-signed or approved artifact needs `--revision revisions/<n>.md`.
