---
type: sdlc/intent
id: docs-reconcile
title: The docs say what the code does
description: "Reconcile every documented claim about a gate, a check or a script with the code that ships it; give the knowledge bundle honest timestamps and complete indexes; move the lessons out of CLAUDE.md into knowledge/ so every model sees them."
stage: plan
status: in-review
author: Luis Siviero (repo owner), drafted with Claude from the 2026-09-04 consensus list (items 10 and 11) and the B12 table of the playbook comparison
approved-by:
approved-on:
supersedes:
record:
resource: https://claude.ai/code/session_01Te8oN2GdvRupSixH4kjR8Y
tags: [docs, okf, knowledge, lessons, reconcile, consensus-item-10, consensus-item-11]
timestamp: 2026-09-05T04:15:00Z
---
# Intent: the docs say what the code does

## Problem
The 2026-09-04 comparison of this kit against the playbook found fifteen documented controls the code does
not deliver (its table B12) and a knowledge bundle whose front matter is not honest: every `docs/` and
`knowledge/` document carries a `timestamp` copied from a template (`2026-09-02T20:00:00Z` or
`2026-09-02T00:00:00Z`) rather than the date it was last written, and the hand-kept indexes lag the files.
Batch A and Batch B (WI-1 to WI-10) closed the controls themselves; the sentences that described the old
behaviour are still on `main`, and a reader of `docs/sdlc/README.md` or a rule fragment is told, for
example, that branch protection guards `main` (it cannot on this plan: HTTP 403), that a 3σ breach opens
a PR (the detector logs and diagnoses), that `/sdlc-incident` appends a row to `docs/sdlc/lessons.md` (that
file is a pointer), or that the rule fragments render "in filename order" (they render by `order`, then
filename).

Two smaller faults ride along and belong to the same sweep because each one misleads the next adopter:

- Six documents carry a front-matter `title` or `description` that contains `: ` unquoted. The kit's own
  parser tolerates it; GitHub's renderer and every strict YAML reader do not, and the owner met the error
  banner on `work/adopter-first-hour/spec.md` from a phone on 2026-09-05. Nothing in `verify.sh` catches it.
- The eight lessons in `CLAUDE.md` live outside the generated block, so `GEMINI.md` and `AGENTS.md` never
  see them; `knowledge/decisions/one-rule-source.md` lists the move to `knowledge/` as undone.

Who is affected: every adopter who reads the docs to learn what the gates do; every Gemini or third-party
session that never sees the lessons; any catalog that indexes the OKF bundle by timestamp. How we know:
consensus items 10 and 11; table B12; the GitHub YAML banner (screenshot, 2026-09-05); a script that
compares each document's `timestamp` with `git log -1 --format=%cI` and finds 29 of 56 differ.

## Proposed outcome
- Every row of table B12 is either true on `main` or its sentence has been rewritten to describe what the
  code does, with the row's verdict recorded in `spec.md` (already fixed by WI-n / rewritten here / code
  changed). Observable: a reviewer can open each cited location and the code it names and find agreement.
- The items PLAN.md WI-11 lists by line (`docs/sdlc/README.md`, `docs/sdlc/rules/index.md`,
  `docs/sdlc/lessons.md`, `knowledge/lessons/index.md`, `/sdlc-incident`, `phase-2-roadmap.md`,
  `spikes/gemini-parity.md`) read true, and the roadmap marks what WI-7 and WI-9 delivered.
- Every `docs/` and `knowledge/` document's `timestamp` equals the commit date of its last change before
  this item (RFC3339), and `docs/sdlc/okf-pairing.md` records the freeze: no new OKF directories until
  `lessons/` or `services/` has content that is not an index.
- Every `index.md` under `knowledge/` lists exactly the files beside it.
- `scripts/verify.sh` fails on a front-matter value a strict YAML reader rejects, and the six documents pass.
- The eight lessons are `knowledge/lessons/<name>.md` documents; `CLAUDE.md` keeps one pointer line per
  lesson inside a rule fragment, so `GEMINI.md` and `AGENTS.md` render the same list; `CLAUDE.md` stays
  under `MAX_CONTEXT_LINES`.
- `.gitattributes` forces LF on `*.md`, `*.py`, `*.yml` and `*.yaml`, so the CRLF drift lesson can be deleted
  once it is impossible.

## Affected users and systems
- Users: the owner; adopters reading `docs/sdlc/`; every Claude, Gemini and third-party session that reads
  a context file.
- Services / repos / data: `docs/sdlc/**`, `knowledge/**`, `docs/sdlc/rules/*.md` (rendered into
  `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`), `.claude/skills/sdlc-incident/SKILL.md`, `.gitattributes`, one new
  checker under `scripts/` with its `scripts/checks/*.sh` entry (control plane: needs the
  `control-plane-approved` label), `.sdlc/active`.

## Constraints
- Must: change the sentence, not the behaviour, unless the spec records a row as a code bug; every
  rewritten claim cites the code it now describes.
- Must: keep every spike's evidence and status; corrections to a spike are additions or one-line
  replacements of a claim, never deletions of reasoning.
- Must: regenerate `CLAUDE.md`, `GEMINI.md`, `AGENTS.md` from the fragments; never hand-edit the block.
- Must not: touch `.claude/hooks/`, `.github/workflows/`, `.sdlc/` (other than `.sdlc/active`),
  `.claude/settings.json`, `scripts/verify.sh`, the two runners; a workflow fix this sweep finds (the
  `sdlc-gate` triage step runs `claude -p` in an untrusted workspace and ignores `permissions.allow`) is
  proposed in the PR description, not made.
- Must not: rewrite the timestamps of `work/**` artifacts (their ledger is the record) or of the handoff
  documents on the `claude/session-handoff` branch.
- Out of scope: the B13 "smaller faults" list (each is a code change with its own work item); building the
  Antigravity adapter; the Gemini CLI account; consensus item 12 (`permissions.deny`/`allow`).

## Risk class
low — documentation, front matter, one warning-to-failing check with a stdlib fallback, and eight lesson
files. Blast radius: what readers believe about the gates. Reversal is a revert. It is the last item of the
plan and gates nothing.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: Should the strict-YAML front-matter check fail `verify.sh` immediately, or warn first like the OKF check
  did? PyYAML is present on the runner and in this session; a machine without it would get a structural
  fallback (quote any value containing `: `).
  A: (proposed by the session on 2026-09-05; edit before approving) Fail immediately. The defect is silent
  and the fix is mechanical (quote the value); a warning would have let the six files sit as they did.
- Q: The lessons move: eight lessons now, not the five the plan counted. One file each, or grouped by theme
  (Windows paths, ledger lines, template spellings)?
  A: (proposed) One file each, named by the mistake (`windows-path-comparison.md`, `ledger-line-format.md`,
  ...); a grouped file would become the next `lessons.md` that nobody splits.
- Q: `knowledge/lessons/index.md` says "one per incident, linked to the incident record". These eight came
  from work items and reviews, not incidents. Loosen the rule?
  A: (proposed) Yes: one lesson per file, linked to the incident, work item or PR that produced it; the
  `/sdlc-incident` rule stays as the incident case of the general one.
