---
type: sdlc/spec
id: parked-marker-on-retired
title: The generated index reads the parked marker only from an approved intent
description: "gen_index.build_item asks next_item.parked_note for a park only when the item's intent.md has status: approved; on any other status the stage cell comes from _stage and the item index carries no Parked: line, so a retired item renders like every other retired item. The helper, the queue and every judging script are untouched; one regression case in a new module is seen red first."
stage: design
# status: draft | in-review | approved | delegated | superseded
status: delegated
reads: intent.md
# approved-by: product owner; tech lead consulted for medium/high risk; set only by a human
approved-by: claude
approved-on: 2026-09-15
# skills-applied: skills loaded as hard constraints while writing this spec
skills-applied: [security-standards]
skills-version: cffcedd
prompt: "/sdlc-run parked-marker-on-retired -> /sdlc-spec, in session_01Vko6ACpeBSiqe6RgsrA8KQ, the successor scheduled by the session that closed risk-detour; from the approved, delegated intent (bad2b14) with its one owner-answered question; a direct read of scripts/gen_index.py (build_item, render_item_index, _stage, render_top_index), scripts/next_item.py (parked_note, resumers, _eligible), scripts/test_gen_index.py (the ParkedMarker fixture and goldens), scripts/test_park_advance.py (a new module composing another module's fixture), .claude/hooks/protect-tests.sh (a new test file stays writable under kind: fix; an existing one is locked), .claude/hooks/require-plan.sh, and main's own work/index.md and work/risk-detour/index.md at bad2b14 where the defect shows. No explorer subagent: the code surface is one function in one file"
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/96
tags: [gen-index, parking, risk-detour, fix, work-index]
timestamp: 2026-09-15T02:33:00Z
---
# Spec: the generated index reads the parked marker only from an approved intent

The intent's one question is answered and is a decision here: the marker reads `parked` only for
`status: approved`; any other status takes its stage from the artifacts and shows no `Parked:` line.

## Requirements (each maps to an intent outcome)
| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R-1 | **A retired item renders like any other retired item.** `gen_index.build_item` sets `item["parked"]` from `next_item.parked_note(entries, next_item.resumers(root))` only when the item's `intent.md` front matter reads `status: approved`; otherwise `item["parked"]` is `None`. Because both renderers read that one key, `work/index.md`'s stage cell is then `_stage(fms)` (`plan`, `spec` or `intent`) and `work/<slug>/index.md` has no `Parked:` line, whatever the ledger's latest `parked:`/`resumed:` line says. | 1 | New module `scripts/test_gen_index_retired.py::RetiredParkedItem::test_a_retired_item_loses_the_marker`: on `test_gen_index._build_two_item_tree` plus the `ParkedMarker` approvers file, an item `retired` whose three artifacts are `superseded` and whose ledger ends `parked:` then the three `-> superseded` lines; the item index equals a golden string with no `Parked:` line and `Last gate:` the `plan.md` retirement, and the top index carries the `retired` row with the stage cell `plan`, three `superseded` cells and the last gate `plan.md -> superseded by alice`. **Red today**: the stage cell reads `parked` and the item index carries `Parked: parked: revision 2: ...`. |
| R-2 | **A park on any non-approved intent is stale by definition.** The condition is `== "approved"`, not `!= "superseded"`: an `in-review` or `draft` intent with a `parked:` line renders no marker either (the owner's answer to the intent's question). | 1, Q | `RetiredParkedItem::test_a_park_on_an_unapproved_intent_is_not_marked`: the parked fixture's intent with `status: in-review` and its unchanged parked ledger renders the stage cell `intent` and no `Parked:` line. **Red today** for the same reason as R-1. |
| R-3 | **A parked, unretired item still renders `parked`.** `scripts/test_gen_index.py::ParkedMarker` passes unchanged, including its resumed half; the two-item goldens are byte-identical. | 2 | `python3 scripts/run_tests.py` green; `git diff origin/main --numstat -- scripts/test_gen_index.py` prints nothing (the file is locked under `kind: fix` and is not touched). |
| R-4 | **`main`'s own index changes by exactly the one row and the one line.** `python3 scripts/gen_index.py` after the fix rewrites `work/index.md` (the `risk-detour` row's stage cell `parked` becomes `plan`) and `work/risk-detour/index.md` (the `Parked:` line and the blank line after it go); every other generated file is byte-identical apart from this item's own `work/parked-marker-on-retired/index.md` and its row, which change because the item gains a spec and a plan. | 3 | `git diff origin/main -- work/index.md` changes three lines, the `risk-detour` row, this item's own row and the front-matter timestamp, and `git diff origin/main --stat -- work/risk-detour/index.md` reads `2 deletions`; `git diff origin/main --name-only -- 'work/*/index.md'` lists only `work/risk-detour/index.md` and `work/parked-marker-on-retired/index.md`; `python3 scripts/gen_index.py --check` ends `INDEX: up to date`. |
| R-5 | **The queue and the judging scripts do not change.** `scripts/next_item.py`, `scripts/check_artifact_chain.py`, `scripts/sign.py`, `scripts/delegated_merge.py`, `scripts/log_ledger.py`, `.claude/hooks/`, `.github/workflows/` and `.sdlc/` are not in the diff; `next_item.parked_note` keeps its contract (latest `parked:`/`resumed:` line on `intent.md`, an approver's `resumed:` only). | Must (constraints) | `git diff origin/main --name-only -- scripts/next_item.py scripts/check_artifact_chain.py scripts/sign.py scripts/delegated_merge.py scripts/log_ledger.py .claude/hooks .github/workflows .sdlc` prints nothing; `python3 scripts/check_detour.py --slug parked-marker-on-retired --diff origin/main` ends `DETOUR: none`. |
| R-6 | **All green.** | 4 | `scripts/verify.sh` ends `VERIFY: PASS (<sha>)`; `python3 scripts/check_artifact_chain.py --base origin/main --slug parked-marker-on-retired` ends `CHAIN: PASS`; `scripts/run_evals.sh` ends `EVALS: N pass, 0 fail, ...`; `python3 scripts/check_okf.py` ends `OKF: N docs, 0 warnings`; the R-1 and R-2 cases were watched red before the condition changed (`knowledge/lessons/a-verifiable-command-fails-before-the-change.md`). |

## Design
### Architecture / data flow
1. `build_item(root, slug)` already parses the three front matters into `fms` and the ledger into
   `entries`, and today computes `"parked": next_item.parked_note(entries, next_item.resumers(root))`
   unconditionally (`scripts/gen_index.py:158`). The change reads `intent_fm.get("status")` (the dict the
   function already holds for the title and description), strips it, and computes the note only when it
   equals `approved`; otherwise the key is `None`.
2. Nothing downstream changes: `render_item_index` prints `Parked: <note>` when `item["parked"]` is truthy
   (`:183`) and `render_top_index` picks `parked` over `_stage` on the same key (`:234`). One condition at
   the source, two renderers healed.
3. `resumers(root)` reads `.sdlc/approvers.yaml` and stays outside the condition, called once per item as
   today, so a malformed approvers file still fails the run loudly on a tree with no approved intent
   (security pass on pull request 100, nit 3). Only the `parked_note` call is gated; there is no other
   observable side effect.

### Interfaces (APIs, events, schemas) — exact shapes
- `build_item` keeps its return shape; `item["parked"]` is `str | None` as today, with `None` for every
  intent status but `approved`.
- No CLI, no flag, no new module beyond the test.

### Data and migrations
- Two generated files on `main` change on the next `gen_index.py` run (R-4). No data, no migration, no
  personal or regulated field (security-standards §4: n/a).

### Failure modes and how they surface
- An intent with no front matter or no `status` key renders no marker (the status reads as `""`). A park
  can only exist on an approved intent, so nothing real is hidden; `scripts/checks/index-drift.sh` byte-compares
  the output on every commit, so a wrong render surfaces as `INDEX: ... drifted` in `verify.sh`.
- `next_item._eligible` refuses a non-approved intent before it reads the park, so the queue never saw the
  defect and cannot see the fix: nothing about admission changes.

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: none. `scripts/gen_index.py` is under `PLAN_REQUIRED_PATHS` and on no locked list, so the delegated
  merge takes the pull request; the intent's constraints keep every judging script out of the diff (R-5).

## Open questions carried from intent.md
- none: the one question is answered on the intent (the marker reads `parked` only for `status: approved`).

## Decisions (ADR-style: context → decision → consequences)
- D1: the condition lives in `build_item`, not in the two renderers. Context: both renderers read one key.
  Decision: gate the key at its source. Consequences: one condition (the intent's "one condition"), the
  golden test in `test_gen_index.py` proves both renderers still agree, and `next_item.parked_note` keeps
  its contract because it is called less, never differently.
- D2: the regression case composes `test_gen_index`'s fixtures from a new module, as `test_park_advance.py`
  composes `test_delegated_merge`'s. Context: `kind: fix` locks `scripts/test_gen_index.py`
  (`.claude/hooks/protect-tests.sh` locks an existing test file and leaves a new one writable). Decision:
  `scripts/test_gen_index_retired.py` imports `_build_two_item_tree`, `_write`, `_outputs_by_path` and the
  parked fixtures and adds its own retired item. Consequences: no existing case is edited; the module is
  discovered by `scripts/run_tests.py`'s `test_*.py` pattern.
- D3: `== "approved"` rather than `!= "superseded"`. Context: the owner's answer. Consequences: R-2 pins it,
  so a later reading that a park on an `in-review` intent should show has to change a test on purpose.

## Gotchas found while reading the codebase
- G-1: `protect-tests.sh` locks a test file the moment it exists, so the new module must be written whole;
  a second edit to it is refused under this plan. Draft it in the scratchpad against the repository's
  `gen_index`, then place it once.
- G-2: `build_item` reads `fms.get("intent.md") or {}`; `cac.front_matter` returns `None` for a missing
  file, so the status read must go through the same `intent_fm` dict, never `fms["intent.md"]["status"]`.
- G-3: the `risk-detour` row on `main` is the live instance of the defect (`work/index.md:32`, stage cell
  `parked`; `work/risk-detour/index.md:14`, `Parked:`); the same `gen_index.py` run that heals it also
  rewrites this item's own index, so R-4 counts both.
- G-4: `ParkedMarker`'s fixture has an intent only; a retired item on `main` has all three artifacts, so the
  R-1 fixture carries three `superseded` artifacts and expects `plan`, the real shape, while R-2 keeps the
  intent-only shape and expects `intent`.

## Not doing
- Any other reading of the ledger by the index; the four filed chain-check defects (intent, out of scope).
- Changing `next_item.parked_note`, its callers in the queue, or any locked script (intent Must not).
- A `Retired:` line or any new marker: a retired item renders exactly as one did before `risk-detour`.
