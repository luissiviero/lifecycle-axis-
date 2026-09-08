---
type: index
title: Lessons
description: One lesson per file, named by the mistake, linked to the incident, work item or PR that produced it.
tags: [okf, index, lessons]
timestamp: 2026-09-05T04:48:42Z
---

# Lessons

One lesson per file, `type: lesson`, linked to the incident, work item or pull request that produced it. `/sdlc-incident`
writes the incident case here (step 4 of the skill); a review or a work item that trips twice writes the general case.
If a lesson changes how the agent should behave, the same PR adds a pointer line to `docs/sdlc/rules/60-lessons.md`,
which renders into `CLAUDE.md`, `GEMINI.md` and `AGENTS.md` (rule 7). `docs/sdlc/lessons.md` is a pointer to this index.

**File naming.** `knowledge/lessons/<name>.md`, named by the mistake; an incident's lesson uses the incident slug,
matching the `work/<slug>/incident.md` that produced it (link back to it with a relative link). One lesson per file; a
single incident that yields more than one distinct lesson gets `<incident-slug>-<n>.md` for the second and later ones.

## Lessons

- [control-plane-unlock-is-advisory.md](control-plane-unlock-is-advisory.md) — rule 3 is advisory in this repo; CI and the owner's review gate the control plane
- [one-path-spelling-in-guards.md](one-path-spelling-in-guards.md) — a path guard compares one spelling; three Windows bypasses
- [test-lib-changes-from-a-second-shell.md](test-lib-changes-from-a-second-shell.md) — a bad `_lib.sh` edit locks the session out of every tool
- [fold-crlf-before-comparing.md](fold-crlf-before-comparing.md) — every `--check` folds CRLF; `.gitattributes` keeps text LF
- [skills-spell-template-headings.md](skills-spell-template-headings.md) — skills and agents spell template fields and headings exactly
- [plan-bullets-start-with-the-path.md](plan-bullets-start-with-the-path.md) — a plan bullet starts with the bare path
- [ledger-slot-holds-status-only.md](ledger-slot-holds-status-only.md) — the ledger's from/to slot holds status values only
- [send-ledger-lines-in-a-fenced-block.md](send-ledger-lines-in-a-fenced-block.md) — ledger lines go to the owner in a fenced block
- [workflow-permissions-name-every-api.md](workflow-permissions-name-every-api.md) — a workflow's `permissions:` block names every API surface its scripts touch
- [stage-new-files-before-verify.md](stage-new-files-before-verify.md) — `git add` new files before `verify.sh`: the front-matter check reads `git ls-files`, and an unquoted colon is what it catches
- [tests-carry-their-own-environment.md](tests-carry-their-own-environment.md) — a test that reads the ambient environment (git identity, the clock) passes here and fails on the runner
- [eval-checks-have-no-blank-lines.md](eval-checks-have-no-blank-lines.md) — a blank line truncates an eval `check:` block into a stub that always passes
- [adopter-context-file-sits-at-the-cap.md](adopter-context-file-sits-at-the-cap.md) — a rules-fragment line is paid for at the adopter's render, which sits at exactly the cap
- [commit-before-the-chain-check.md](commit-before-the-chain-check.md) — staged work is invisible to the chain check; commit first, and since work/run-queue-followups it refuses rather than passing
