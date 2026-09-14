---
type: sdlc/plan
id: approve-tap-regenerates-index
title: Regenerate inside the committer, widen its allowlist to the generated indexes, prove both with six cases
description: "scripts/approve_dispatch.py --commit renders every index with gen_index.render_all before it judges the tree, allows work/index.md and work/<dir>/index.md, stages what git status reports, refuses an index-only diff, and says so in its text; six new cases in scripts/test_approve_dispatch.py, three seen red before the change."
stage: build
# status: draft | in-review | approved | delegated | superseded  (require-plan.sh refuses code edits until approved)
status: delegated
# kind: feature | fix  (fix: protect-tests.sh refuses edits to existing test files)
kind: feature
reads: spec.md
# approved-by: engineer for routine; tech lead/architect for medium/high risk; set only by a human
approved-by: claude
approved-on: 2026-09-14
risk-class: low
record:
resource: https://github.com/luissiviero/lifecycle-axis-/commit/c0aa58c
tags: [approvals, workflow-dispatch, gen-index, index-drift, verify, delegated-mode]
timestamp: 2026-09-14T03:00:00Z
---
# Plan: the approval tap regenerates the indexes it leaves stale (from intent.md 2026-09-08)

`kind: feature`, not `fix`, for the same load-bearing reason `work/run-queue-followups/plan.md` gives:
`kind: fix` closes `protect-tests.sh` over existing test files, and every case this item adds belongs in
`scripts/test_approve_dispatch.py`, the file that already tests the committer, as the intent requires. The
discipline of a fix is kept regardless: step 1 writes the cases and watches three of them fail before step
2 writes any code.

No engineer interview: the owner is the only human and works from a phone, so the repository's own record
stood in for it (`CLAUDE.md` conventions, the lessons named below, the spec's gotchas G-1 to G-9).

## Files that change
- scripts/approve_dispatch.py — `INDEX_RE` and `is_allowed(path, slug)` replacing the set membership in `unexpected_paths` (R-3); `regenerate(root)` calling `gen_index.render_all` and writing changed files with the generator's own `open(..., encoding="utf-8", newline="\n")`, printing the R-8 line (R-1, R-2, R-8); `commit()` reordered to regenerate → stray check → stage what `git status` reported → nothing-staged check minus generated paths → commit (R-1, R-4, R-5); the module docstring's `--commit` paragraph and the `CHAIN_FILES` comment rewritten (R-6)
- scripts/test_approve_dispatch.py — a fixture helper that adds a second item with a stale committed index, and six new `Commit` cases: `test_commit_regenerates_both_indexes`, `test_a_stale_index_of_another_item_is_committed_too`, `test_generated_indexes_of_any_item_are_allowed`, `test_index_lookalikes_are_stray`, `test_a_stray_beside_regenerated_indexes_still_aborts`, `test_index_only_changes_do_not_make_a_commit` (R-1 to R-5, R-8); no existing case edited
- work/approve-tap-regenerates-index/spec.md — signed under the grant; body edits only if the review finds a line the code proves wrong
- work/approve-tap-regenerates-index/plan.md — this plan; its deviations log
- work/approve-tap-regenerates-index/log.md — one ledger line per gate
- work/approve-tap-regenerates-index/index.md — regenerated
- work/index.md — regenerated

## Release-gated
(none) — no path under `RELEASE_GATED_PATHS` (`migrations infra terraform helm`) is touched. `scripts/approve_dispatch.py`
is under `PLAN_REQUIRED_PATHS` and is neither protected nor on the policy's `locked-paths`, which is what
lets the merge workflow merge this pull request without a click.

## Order of work (each step independently verifiable)
1. **The failing cases first.** Add to `scripts/test_approve_dispatch.py` a helper `add_other_item(root, stale_index)`
   that writes `work/other/intent.md` and, when asked, a hand-written `work/other/index.md`, and commits both
   with the fixture's own identity (`knowledge/lessons/tests-carry-their-own-environment.md`). Then the six
   cases the spec names, in `Commit`. Verify: `python3 scripts/run_tests.py -p test_approve_dispatch.py`
   shows exactly three failures — `test_commit_regenerates_both_indexes` (R-1, R-8),
   `test_a_stale_index_of_another_item_is_committed_too` (R-2) and
   `test_generated_indexes_of_any_item_are_allowed` (R-3's positive half) — and the other three new cases
   green, because today's committer already refuses lookalikes, strays and an empty diff. A new case that is
   green here for a reason other than that is not exercising the change and the step is not done
   (`knowledge/lessons/a-verifiable-command-fails-before-the-change.md`).
2. **The predicate.** `INDEX_RE = re.compile(r"work/([A-Za-z0-9_][A-Za-z0-9._-]*)/index\.md")`,
   `is_allowed(path, slug)` true for `allowed_paths(slug)` membership, `work/index.md`, or an `INDEX_RE`
   fullmatch; `unexpected_paths` uses it; a comment beside `INDEX_RE` says why its segment class is the
   generator's and not `SLUG_RE` (spec D4, G-2). Verify: both R-3 cases green; `SlugContainment` unchanged
   and green.
3. **Regenerate, stage, refuse an index-only diff.** `regenerate(root)` as the spec's Interfaces describe,
   called first in `commit()`; the R-8 stdout line; staging built from the porcelain paths rather than the
   fixed `present` list (spec D5); the nothing-staged check subtracts the paths `is_allowed` accepts as
   generated (spec D3). Verify: the whole module green, 32 cases; `test_nothing_to_stage_is_refused` and
   `test_active_and_index_are_allowed` green without edits (spec G-3, G-4).
4. **The text.** Rewrite the docstring's `--commit` paragraph and the `CHAIN_FILES` comment so both name the
   regeneration that happens inside `--commit` and the two generated paths. Verify: the two R-6 greps.
5. **Regenerate and verify the whole loop.** `python3 scripts/gen_index.py`, `python3 scripts/gen_context_files.py`,
   `git add` every changed file (`knowledge/lessons/stage-new-files-before-verify.md`), `scripts/verify.sh`,
   commit, then `python3 scripts/check_artifact_chain.py --base origin/main --slug approve-tap-regenerates-index`
   (`knowledge/lessons/commit-before-the-chain-check.md`), `scripts/run_evals.sh`, `python3 scripts/check_okf.py`,
   and the R-7 diff: `git diff origin/main --stat -- .github/workflows/approve.yml scripts/approve.py scripts/gen_index.py`
   prints nothing.
6. **Draft pull request, review, ready.** Push to this session's `claude/` branch, open the draft with
   `[approve-tap-regenerates-index]` in the title and `Work-Item: approve-tap-regenerates-index` in the
   body, paste the four last lines; `/sdlc-review` with `plan-reviewer` and `security-reviewer` on a model
   other than the writer's, fix what they find with evidence, then ready. The delegated-merge workflow
   merges when its printed conditions hold; `sdlc-run` step 7 follows.

## Risks
- Risk: `import gen_index` pulls `check_artifact_chain` and `log_ledger` into the committer's process, and
  one of them does something at import time the runner's environment lacks → mitigation: the probe of
  2026-09-14 ran the generator from a bare temp root with no `.sdlc/`, and `test_approve_dispatch.py`
  imports `approve_dispatch` in every case, so an import-time failure shows in step 1, on this machine,
  before any push.
- Risk: the runner's tree differs from a session's, so `render_all` renders something the session did not
  → mitigation: `actions/checkout` gives a full working tree of the dispatch ref (depth 1 is history, not
  files), the generator reads only files under `work/`, and R-1 pins byte-identity against the generator's
  own `--check` on the committed tree.
- Risk: a regenerated index the predicate rejects makes every tap refuse → mitigation: only a directory
  under `work/` with a leading dot could produce one; none exists, the refusal would name the path, and
  the older approval routes stay open.
- Risk: the R-8 stdout line or the traceback of an `OSError` lands somewhere the owner cannot see →
  mitigation: the Commit step's stdout and stderr are the run log, the same place `git push`'s output
  already goes.
- What this could break: the tap itself, since every approval and every grant goes through `--commit`. A
  defect here fails the run before its push and leaves `main` as it was; nothing lands half-way, because
  the guard runs before `git add` and the commit is one call.
- Options considered and not taken: a regeneration step in the workflow (rejected by the owner in the
  intent: a protected path ends the queue); refusing on another item's drift, or staging around it (both
  rejected by the owner: the first fails the tap whenever `main` is already drifted, the second leaves
  the drift where it stalls the delegated merge); extracting the write loop into `gen_index.write_all`
  (spec D1: a third file for four lines, and `--check` already proves the two write routes agree);
  building the index predicate on `SLUG_RE` (spec D4, G-2: `work/_example/index.md` is tracked and would
  make the tap refuse the moment it drifted); `kind: fix` (locks the test file this item must add to).

## Proof
- `scripts/verify.sh` green, ending `VERIFY: PASS (<sha>)`
- Spec rows → tests: R-1 → `Commit::test_commit_regenerates_both_indexes`;
  R-2 → `Commit::test_a_stale_index_of_another_item_is_committed_too`;
  R-3 → `Commit::test_generated_indexes_of_any_item_are_allowed` and `Commit::test_index_lookalikes_are_stray`;
  R-4 → `Commit::test_a_stray_beside_regenerated_indexes_still_aborts` plus the three existing stray cases unmodified;
  R-5 → `Commit::test_index_only_changes_do_not_make_a_commit` plus `Commit::test_nothing_to_stage_is_refused` unmodified;
  R-6 → `grep -c "gen_index" scripts/approve_dispatch.py` at least 3 and `grep -c "is regenerated in the same tree" scripts/approve_dispatch.py` 0;
  R-7 → `git diff origin/main --stat -- .github/workflows/approve.yml scripts/approve.py scripts/gen_index.py` empty, the pull request's file list, `ActorCheck`/`Mode`/`SlugContainment` unmodified, `CHAIN: PASS` with `--slug approve-tap-regenerates-index`;
  R-8 → the stdout assertions inside the R-1 and R-5 cases;
  R-9 → the four last lines pasted in the pull request, case count 26 before and 32 after.
- Manual / browser / screenshot / eval: none new; the next real tap on `main` after the merge is the
  production observation the intent names (its commit touches both indexes and `gen_index.py --check`
  on it is up to date), and the handoff's task state should record it when it happens.

## Rollback
Revert the commit. The committer returns to staging its fixed list and the allowlist to its former set;
no data, format or workflow changes persist, and no other file imports the new functions.
`scripts/approve_dispatch.py` is not a locked path, so the revert could itself be a delegated item.

## Deviations log (append during implementation; same commit as the deviation)
- 
