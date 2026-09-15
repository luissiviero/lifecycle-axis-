---
type: sdlc/plan
id: parked-marker-on-retired
title: Two red cases in a new module, then one condition in build_item, then the regeneration
description: "scripts/test_gen_index_retired.py (new, two cases composing test_gen_index's fixtures, both watched red first), then build_item in scripts/gen_index.py gates the parked_note call on the intent reading status: approved, then python3 scripts/gen_index.py heals the risk-detour row and index on main; kind fix, so no existing test file is touched."
stage: build
# status: draft | in-review | approved | delegated | superseded  (require-plan.sh refuses code edits until approved)
status: delegated
# kind: feature | fix  (fix: protect-tests.sh refuses edits to existing test files)
kind: fix
reads: spec.md
# approved-by: engineer for routine; tech lead/architect for medium/high risk; set only by a human
approved-by: claude
approved-on: 2026-09-15
risk-class: low
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/96
tags: [gen-index, parking, risk-detour, fix, work-index]
timestamp: 2026-09-15T02:36:00Z
---
# Plan: two red cases in a new module, then one condition, then the regeneration (from intent.md 2026-09-15)

`kind: fix`, as the intent requires: `protect-tests.sh` locks every existing test file and eval case for
the life of this plan, so the regression cases live in a new module the hook leaves writable (spec D2,
G-1). The module is written whole and placed once.

No engineer interview: the owner is the only human and works from a phone, so the repository's own record
stood in for it (`CLAUDE.md` conventions, the lessons named under Risks, the spec's gotchas G-1 to G-4).

## Files that change
- scripts/test_gen_index_retired.py — new; `class RetiredParkedItem` on `test_gen_index._build_two_item_tree` plus the `ParkedMarker` approvers file: `test_a_retired_item_loses_the_marker` (an item `retired` with three `superseded` artifacts and a ledger that ends `parked:` then three `-> superseded` lines; golden item index with no `Parked:` line, the top-index row with stage `plan`) and `test_a_park_on_an_unapproved_intent_is_not_marked` (the parked fixture's intent as `status: in-review` with the same parked ledger; stage `intent`, no `Parked:` line) (spec R-1, R-2)
- scripts/gen_index.py — `build_item`: the `"parked"` value becomes `next_item.parked_note(entries, next_item.resumers(root))` only when `(intent_fm.get("status") or "").strip() == "approved"`, else `None`; the comment above it says why (spec R-1, D1, D3)
- work/risk-detour/index.md — regenerated: the `Parked:` line and its blank line go (spec R-4)
- work/index.md — regenerated: the `risk-detour` row's stage cell `parked` becomes `plan`; this item's own row (spec R-4)
- work/parked-marker-on-retired/spec.md — signed under the grant
- work/parked-marker-on-retired/plan.md — this plan; its deviations log
- work/parked-marker-on-retired/log.md — one ledger line per gate
- work/parked-marker-on-retired/index.md — regenerated

Not in the list, on purpose: `scripts/test_gen_index.py` (locked under `kind: fix`, and spec R-3 requires it
untouched), `scripts/next_item.py` (a locked path since `796d47b`; its `parked_note` contract is the queue's),
and every judging script, hook, workflow and `.sdlc/` file (spec R-5).

## Release-gated
(none) — no path under `RELEASE_GATED_PATHS` (`migrations infra terraform helm`) is touched. `scripts/gen_index.py`
is under `PLAN_REQUIRED_PATHS` and on no protected or locked list, which is what lets the delegated-merge
workflow merge this pull request without a click.

## Order of work (each step independently verifiable)
1. **The failing cases first.** Draft `scripts/test_gen_index_retired.py` in the scratchpad against the
   repository's `gen_index` (G-1: the hook locks the file the moment it exists under this plan), then place
   it. Verify: `python3 -m unittest discover -s scripts -p test_gen_index_retired.py` shows exactly two
   failures, both on the stage cell or the `Parked:` line, before step 2
   (`knowledge/lessons/a-verifiable-command-fails-before-the-change.md`); commit the red module on its own so
   the record holds it.
2. **The condition.** In `build_item`, read the intent's status from the `intent_fm` dict the function
   already holds (G-2) and compute the note only for `approved`. Verify: the two new cases green;
   `scripts/test_gen_index.py` green unmodified (`ParkedMarker`, `GoldenRender`, `Idempotence`, `CheckMode`).
3. **Regenerate and verify the whole loop.** `python3 scripts/gen_index.py`, then `git add` every changed
   file (`knowledge/lessons/stage-new-files-before-verify.md`), `scripts/verify.sh`, commit, then
   `python3 scripts/check_artifact_chain.py --base origin/main --slug parked-marker-on-retired`
   (`knowledge/lessons/commit-before-the-chain-check.md`), `scripts/run_evals.sh`, `python3 scripts/check_okf.py`,
   `python3 scripts/check_detour.py --slug parked-marker-on-retired --diff origin/main`, and the R-4 counts:
   `git diff origin/main --stat -- work/index.md work/risk-detour/index.md` and
   `git diff origin/main --name-only -- 'work/*/index.md'`.
4. **Draft pull request, review, ready.** Open the draft on this session's `claude/` branch on the first
   push, `[parked-marker-on-retired]` in the title and `Work-Item: parked-marker-on-retired` in the body,
   with the four last lines and the red run from step 1 pasted. `/sdlc-review` with `plan-reviewer` and
   `security-reviewer` on a model other than the writer's, fix what they find with evidence, post the
   findings with `Important: 0 | Nits: <m>`, then ready. The delegated-merge workflow merges when its printed
   conditions hold; `sdlc-run` step 7 follows.

## Risks
- Risk: the condition is put in a renderer instead of `build_item`, and the two renderers disagree →
  mitigation: spec D1 names the function; R-1's case asserts both outputs from one `render_all` call.
- Risk: a parked, live item loses its marker → mitigation: `ParkedMarker` is the pin and is locked under
  this plan, so it cannot be edited into passing; R-3 requires it green unmodified.
- Risk: the new module drifts from `test_gen_index`'s fixtures if those change later → mitigation: it
  imports them by name, as `test_park_advance.py` imports `test_delegated_merge`'s, so a rename fails
  loudly at import rather than silently passing.
- What this could break: nothing that judges a merge or a signature. The only production effect is two
  generated files on `main`, byte-compared by `scripts/checks/index-drift.sh` on every commit.
- Options considered and not taken: `!= "superseded"` (spec D3: the owner chose `approved` only);
  changing `next_item.parked_note` to read the intent's status (a locked path, and the queue already
  refuses a non-approved intent before it reads the park); a case added to `scripts/test_gen_index.py`
  (locked under `kind: fix`; the intent names the new module).

## Proof
- `scripts/verify.sh` green, ending `VERIFY: PASS (<sha>)`
- Spec rows → tests: R-1 → `RetiredParkedItem::test_a_retired_item_loses_the_marker`;
  R-2 → `RetiredParkedItem::test_a_park_on_an_unapproved_intent_is_not_marked`;
  R-3 → `ParkedMarker::test_a_parked_item_is_marked_in_both_indexes` and `GoldenRender` unmodified, `git diff origin/main --numstat -- scripts/test_gen_index.py` empty;
  R-4 → the two `git diff origin/main` commands in step 3 and `INDEX: up to date`;
  R-5 → the `git diff origin/main --name-only` over the judging paths empty, `DETOUR: none` on `--diff origin/main`;
  R-6 → the four last lines pasted in the pull request, the step 1 red run pasted beside them.
- Manual / browser / screenshot / eval: none new; `main`'s `work/index.md` after the merge shows the
  `risk-detour` row with stage `plan`, the production observation the intent names.

## Rollback
Revert the commits. `build_item` returns to computing the note unconditionally and the next
`gen_index.py` run restores the two lines; no data, format or workflow changes persist, and no other file
imports anything new. `scripts/gen_index.py` is not a locked path, so the revert could itself be a
delegated item.

## Deviations log (append during implementation; same commit as the deviation)
- 2026-09-15 — the signed spec's body was corrected in two acceptance-test sentences after step 3
  measured them: R-1 quoted the golden row as `[retired](retired/index.md)`, which `check_okf.py` reads as
  a Markdown link to a file that does not exist (`OKF: 227 docs, 1 warnings`), so the row is now described
  in words; R-4 counted `1 insertion, 1 deletion` on `work/index.md` against `origin/main`, which is the
  count against the commit before the fix, while against `origin/main` the file changes three lines (the
  `risk-detour` row, this item's own row and the timestamp, the two extra lines R-4's prose already
  excepts), so the sentence now names the three. No requirement, design line or test changed; the file
  list said `spec.md` was signed only, so this is logged. 1 of 5.
