---
type: sdlc/intent
id: parked-marker-on-retired
title: A retired item still reads `parked` in the generated index
description: "gen_index.py marks an item parked from its ledger's latest parked:/resumed: line alone, so a retired item whose last such line is a park keeps the parked stage cell and the Parked: line after its intent is superseded; the marker should yield to the retirement."
stage: plan
# status: draft | in-review | approved | delegated | superseded
status: in-review
author: Luis Siviero (repo owner), in the session that closed risk-detour on 2026-09-15; drafted by Claude from the owner's choice of a separate low item over folding it into a later defect intent
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
# detour-of: the slug of the parked item this intent is the remainder of, if any (mode stays supervised; the class is the record's)
detour-of:
# record: legacy system id (Jira/ServiceNow) if that system holds a copy
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/96
tags: [gen-index, parking, risk-detour, fix, work-index]
timestamp: 2026-09-15T02:20:28Z
---
# Intent: a retired item still reads `parked` in the generated index

## Problem
Observed on `main` at `fd39dd0`, minutes after the owner retired `risk-detour` by tap: `work/index.md`'s row
for the item reads `parked | superseded | superseded | superseded` in its stage, intent, spec and plan cells,
and `work/risk-detour/index.md:14` still carries `Parked: parked: ready PR #96; click needed
(.claude/skills/sdlc-run/SKILL.md)`. The item is finished, not parked: its three artifacts are `superseded`
and its ledger's last three lines are the retirement.

Cause: `scripts/gen_index.py:234` writes `parked` whenever `next_item.parked_note(entries, resumers(root))`
returns a note, and that helper reads only the latest `parked:`/`resumed:` line on `intent.md`
(`work/risk-detour` R-3, D3). A retirement writes `approved -> superseded` lines, which are neither word,
so the park stays the latest state the index can see. The queue is unaffected: `next_item._eligible`
refuses a non-`approved` intent before it reads the park, so a retired item is never offered whatever its
ledger says. The defect is the owner-facing marker only.

The owner asked, in the same session: "Is it trivial enough that we can fix it before opening a new
session?" The code change is; the route to `main` needs its own item, because `scripts/` is under
`PLAN_REQUIRED_PATHS` and no active plan lists `gen_index.py`.

## Proposed outcome
- A retired item renders like any other retired item. Observable: on a fixture whose intent is
  `superseded` and whose ledger's latest `parked:`/`resumed:` line is `parked:`, `work/index.md`'s stage
  cell is the stage the artifacts give (`plan`, `spec` or `intent`, from `_stage`) and the item index has
  no `Parked:` line. A regression test in a new module (the item is `kind: fix`, so existing test files
  are locked) that is red on today's code.
- A parked, unretired item still renders `parked`. Observable: `scripts/test_gen_index.py::ParkedMarker`
  passes unchanged.
- `main`'s own index changes by exactly the one row and the one line. Observable: `python3
  scripts/gen_index.py` after the fix rewrites `work/index.md` (the `risk-detour` row's stage cell becomes
  `plan`) and `work/risk-detour/index.md` (the `Parked:` line and its blank line go), and nothing else;
  `python3 scripts/gen_index.py --check` ends `INDEX: up to date` afterwards.
- All green: `VERIFY: PASS`, `CHAIN: PASS`, `EVALS: 0 fail`, `OKF: 0 warnings`.

## Affected users and systems
- Users: the owner, who reads `work/index.md` first; every session that reads the index for state.
- Services / repos / data: `scripts/gen_index.py` (the one condition); a new `scripts/test_gen_index_retired.py`;
  `work/index.md` and `work/risk-detour/index.md` (regenerated); the item's own artifacts.

## Constraints
- Must: keep `next_item.parked_note` as it is. The queue reads it too, and its contract (latest
  `parked:`/`resumed:` line, an approver's `resumed:` only) is `work/risk-detour` R-3's; the index, not the
  helper, decides what a park means for a retired item.
- Must: `kind: fix`, so the regression test is written and seen red before the condition changes.
- Must not: change `check_artifact_chain.py`, `sign.py`, `delegated_merge.py`, `next_item.py`, the hooks,
  the workflows or `.sdlc/`; write `approved`; move `.sdlc/active` from a session.
- Out of scope: any other reading of the ledger by the index; the four filed chain-check defects.

## Risk class
low — one condition in a generator whose output is byte-compared by `scripts/checks/index-drift.sh`, with a
golden test; nothing that judges a merge or a signature changes; the only production effect is two
generated files on `main`. `scripts/gen_index.py` is under `PLAN_REQUIRED_PATHS` and on no locked list, so a
delegated pull request for this item merges under the workflow and its advance runs (the first delegated
merge since `risk-detour` landed, which the handoff's Task state is waiting to observe).

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: should the marker yield only when the intent is `superseded`, or whenever it is anything but
  `approved`? Proposed: only when `approved`, the one status under which a park can exist; a park line on
  an intent in any other status is stale by definition, so the marker reads `parked` only for
  `status: approved` and the stage cell otherwise comes from `_stage`.
  A: agreed (owner, 2026-09-15): the marker reads `parked` only for `status: approved`; any other status takes its stage from the artifacts and shows no `Parked:` line.
