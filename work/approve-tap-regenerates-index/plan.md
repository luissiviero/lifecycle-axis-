---
type: sdlc/plan
id: approve-tap-regenerates-index
title: Regenerate inside the committer, heal foreign drift only on the default branch, judge a rename at both ends, prove it with thirteen cases
description: "scripts/approve_dispatch.py --commit decides its route from runner-set values, renders every index with gen_index.render_all, writes and allows other items' indexes only on the default branch, stages what one git status run reported, refuses an index-only diff before staging, judges a rename's source, and says so in its text; thirteen new cases in scripts/test_approve_dispatch.py, ten seen red before the code."
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
timestamp: 2026-09-14T03:20:00Z
---
# Plan: the approval tap regenerates the indexes it leaves stale (from intent.md 2026-09-08)

`kind: feature`, not `fix`, for the same load-bearing reason `work/run-queue-followups/plan.md` gives:
`kind: fix` closes `protect-tests.sh` over existing test files, and every case this item adds belongs in
`scripts/test_approve_dispatch.py`, the file that already tests the committer, as the intent requires. The
discipline of a fix is kept regardless: step 1 writes the cases and watches them fail before step 2 writes
any code.

No engineer interview: the owner is the only human and works from a phone, so the repository's own record
stood in for it (`CLAUDE.md` conventions, the lessons named below, the spec's gotchas G-1 to G-12).

Revised once after the first review round (`revisions/1.md`): the heal of other items' indexes is scoped
to the default branch, the route is decided from runner-set values with a narrow fallback, a rename is
judged at both ends, and one `git status` run feeds both the guard and the staging. Six cases were built
under the first signed plan (commits 98daa7c and f8b0e1d); this revision adds seven.

## Files that change
- scripts/approve_dispatch.py — `is_default_branch` shared by `check_actor` and the route (R-7, R-11); `event_default_branch` and `route` reading `GITHUB_REF_NAME`, `GITHUB_REF_TYPE` and the event payload, failing narrow (R-11); `INDEX_RE`, `own_index`, `is_generated_index` and `is_allowed(path, slug, allowed, wide)` (R-3); `changed_paths` returning the judged and staged lists from one status run (R-10, spec D5); `unexpected_paths(slug, root, changed, wide)` validating the slug first (R-3); `regenerate(root, writable)` writing only what the route allows and printing the three R-8 lines; `commit(..., ref, default_branch)` ordered route → regenerate → stray check → index-only refusal → stage → commit (R-1, R-2, R-4, R-5); `main()` threading `--ref` and `--default-branch` into `commit()` (R-7); the docstring's `--commit` paragraph and the `CHAIN_FILES` comment rewritten (R-6)
- scripts/test_approve_dispatch.py — fixture helper `add_other_item`, a stdout/stderr-capturing `run_commit_capturing`, and thirteen new `Commit` cases: `test_commit_regenerates_both_indexes`, `test_a_stale_index_of_another_item_is_committed_too`, `test_on_another_ref_only_the_items_indexes_are_written`, `test_generated_indexes_of_any_item_are_allowed`, `test_a_foreign_index_is_a_stray_on_the_narrow_route`, `test_index_lookalikes_are_stray`, `test_a_traversing_slug_is_refused_on_a_clean_tree`, `test_a_stray_beside_regenerated_indexes_still_aborts`, `test_index_only_changes_do_not_make_a_commit`, `test_unknown_ref_takes_the_narrow_route`, `test_a_malformed_event_payload_takes_the_narrow_route`, `test_a_rename_source_is_judged_too`, `test_cli_threads_ref_and_default_branch_into_commit` (R-1 to R-5, R-7, R-8, R-10, R-11); no existing case edited
- work/approve-tap-regenerates-index/spec.md — signed under the grant, re-signed under revision 1
- work/approve-tap-regenerates-index/plan.md — this plan; its deviations log; re-signed under revision 1
- work/approve-tap-regenerates-index/revisions/1.md — new; the consensus record, two `verdict: revise` sections on Opus against a Fable writer
- work/approve-tap-regenerates-index/revisions/index.md — new; a revisions directory without one is an OKF warning
- work/approve-tap-regenerates-index/log.md — one ledger line per gate
- work/approve-tap-regenerates-index/index.md — regenerated
- work/index.md — regenerated

## Release-gated
(none) — no path under `RELEASE_GATED_PATHS` (`migrations infra terraform helm`) is touched. `scripts/approve_dispatch.py`
is under `PLAN_REQUIRED_PATHS` and is neither protected nor on the policy's `locked-paths`, which is what
lets the merge workflow merge this pull request without a click.

## Order of work (each step independently verifiable)
1. **The failing cases first.** Under the first signed plan: the helper `add_other_item(root, stale_index)`
   (renders every index up to date, then overwrites `work/other/index.md` with stale text, commits with the
   fixture's own identity, `knowledge/lessons/tests-carry-their-own-environment.md`) and six cases, of
   which four were red on the code before the item (deviation 1). Under revision 1: seven more cases, of
   which six must be red against 69c460f before step 2 — `test_on_another_ref_only_the_items_indexes_are_written`
   and `test_unknown_ref_takes_the_narrow_route` and `test_a_malformed_event_payload_takes_the_narrow_route`
   (the foreign index is committed today), `test_a_foreign_index_is_a_stray_on_the_narrow_route` (allowed
   today), `test_a_rename_source_is_judged_too` (the source is dropped today), `test_cli_threads_ref_and_default_branch_into_commit`
   (`commit()` has no such parameters today, so the patched call records none) — and one,
   `test_a_traversing_slug_is_refused_on_a_clean_tree`, is green since f8b0e1d and is mutation-tested red
   by removing the up-front `allowed_paths` call, the result recorded in the pull request. The wide-route
   cases (`test_a_stale_index_of_another_item_is_committed_too`, `test_generated_indexes_of_any_item_are_allowed`,
   `test_index_only_changes_do_not_make_a_commit`) gain their explicit route argument in this step and
   stay green. Verify: `python3 scripts/run_tests.py -p test_approve_dispatch.py` shows exactly those six
   failures (`knowledge/lessons/a-verifiable-command-fails-before-the-change.md`).
2. **The route and the predicate.** `is_default_branch` (extracted from `check_actor`'s comparison,
   behaviour unchanged, `Mode` green), `event_default_branch`, `route`, `own_index`, `is_allowed` with
   `wide`, `unexpected_paths` with `changed` and `wide`. Verify: R-3's four cases and R-11's two green;
   `SlugContainment` and `Mode` unchanged and green.
3. **Two lists from one status run, and a rename's source.** `changed_paths` returns `(judged, staged)`;
   `commit()` calls it once and passes the judged list to `unexpected_paths` and the staged list to
   `git add`. Verify: `test_a_rename_source_is_judged_too` green; the existing stray cases green.
4. **Regenerate by route, refuse index-only before staging, thread the CLI.** `regenerate(root, writable)`
   with the three stdout lines; `commit()` in the spec's order with `ref` and `default_branch`; `main()`
   passes `a.ref` and `a.default_branch`. Verify: the whole module green, 39 cases;
   `test_nothing_to_stage_is_refused` and `test_active_and_index_are_allowed` green without edits.
5. **The text.** Rewrite the docstring's `--commit` paragraph and the `CHAIN_FILES` comment so both name the
   regeneration, the two generated paths and the two routes. Verify: the three R-6 greps.
6. **Regenerate and verify the whole loop.** `python3 scripts/gen_index.py`, `python3 scripts/gen_context_files.py`,
   `git add` every changed file (`knowledge/lessons/stage-new-files-before-verify.md`), `scripts/verify.sh`,
   commit, then `python3 scripts/check_artifact_chain.py --base origin/main --slug approve-tap-regenerates-index`
   (`knowledge/lessons/commit-before-the-chain-check.md`), `scripts/run_evals.sh`, `python3 scripts/check_okf.py`,
   and the R-7 check: `git diff origin/main --name-only` lists only the two code files and this item's
   directory.
7. **Draft pull request, review, ready.** Already open as #83 on this session's `claude/` branch, with
   `[approve-tap-regenerates-index]` in the title and `Work-Item: approve-tap-regenerates-index` in the
   body. After step 6: paste the four last lines, run `/sdlc-review` again with `plan-reviewer` and
   `security-reviewer` on a model other than the writer's, fix what they find with evidence, post the
   findings with `Important: 0 | Nits: <m>`, then ready. The delegated-merge workflow merges when its
   printed conditions hold; `sdlc-run` step 7 follows.

## Risks
- Risk: `import gen_index` pulls `check_artifact_chain` and `log_ledger` into the committer's process, and
  one of them does something at import time the runner's environment lacks → mitigation: the only
  import-time side effect is a `git rev-parse` from the cwd (spec G-5), which the probe ran from a bare
  temp root, and `test_approve_dispatch.py` imports `approve_dispatch` in every case, so an import-time
  failure shows in step 1, on this machine, before any push.
- Risk: the runner's tree differs from a session's, so `render_all` renders something the session did not
  → mitigation: `actions/checkout` gives a full working tree of the dispatch ref (depth 1 is history, not
  files), the generator reads only files under `work/`, and R-1 pins byte-identity against the generator's
  own `--check` on the committed tree.
- Risk: the route is decided wrong. A tap on `main` read as narrow leaves foreign drift there (today's
  behaviour, visible in the run log's `left ... unwritten` line); a tap on a branch read as wide commits a
  foreign index and turns the branch's pull request red → mitigation: the two inputs are runner-set and
  the second is the field the role gate already trusts; every malformed value yields narrow, the safe
  direction; `GITHUB_REF_TYPE` excludes a tag named like the branch; R-11's cases cover unset, missing,
  unparsable, wrong-shaped and null values.
- Risk: the R-8 stdout lines or the traceback of an `OSError` land somewhere the owner cannot see →
  mitigation: the Commit step's stdout and stderr are the run log, the same place `git push`'s output
  already goes.
- What this could break: the tap itself, since every approval and every grant goes through `--commit`. A
  defect here fails the run before its push and leaves the ref as it was; nothing lands half-way, because
  every refusal returns before `git add` and the commit is one call.
- Options considered and not taken: a regeneration step or a default-branch line in the workflow
  (rejected by the owner in the intent, and again in revision 1: a protected path ends the queue, and the
  runner already provides both values); widening `own_artifact` in `check_artifact_chain.py` so a foreign
  index stays in-progress (a `locked-paths` file, and the one-item-per-pull-request rule it enforces is
  what `knowledge/lessons/human-commits-leave-indexes-stale.md` relies on); dropping the foreign-index
  heal everywhere (the strictly smallest change, rejected because it discards an owner-answered intent
  outcome); refusing on another item's drift, or staging around it (both rejected by the owner);
  extracting the write loop into `gen_index.write_all` (spec D1); building the index predicate on
  `SLUG_RE` (spec D4, G-2); scoping only `regenerate`'s writes and not the staging predicate (spec D7:
  a containment that holds only because a runner checkout is fresh); `kind: fix` (locks the test file
  this item must add to).

## Proof
- `scripts/verify.sh` green, ending `VERIFY: PASS (<sha>)`
- Spec rows → tests: R-1 → `Commit::test_commit_regenerates_both_indexes`;
  R-2 → `Commit::test_a_stale_index_of_another_item_is_committed_too` and `Commit::test_on_another_ref_only_the_items_indexes_are_written`;
  R-3 → `Commit::test_generated_indexes_of_any_item_are_allowed`, `Commit::test_a_foreign_index_is_a_stray_on_the_narrow_route`, `Commit::test_index_lookalikes_are_stray` and `Commit::test_a_traversing_slug_is_refused_on_a_clean_tree` (mutation-tested);
  R-4 → `Commit::test_a_stray_beside_regenerated_indexes_still_aborts` plus the three existing stray cases unmodified;
  R-5 → `Commit::test_index_only_changes_do_not_make_a_commit` plus `Commit::test_nothing_to_stage_is_refused` unmodified;
  R-6 → the three greps on `scripts/approve_dispatch.py`;
  R-7 → `git diff origin/main --name-only`, the pull request's file list, `ActorCheck`/`Mode`/`SlugContainment` unmodified, `Commit::test_cli_threads_ref_and_default_branch_into_commit`, `CHAIN: PASS` with `--slug approve-tap-regenerates-index`;
  R-8 → the verbatim stdout assertions inside the R-1, R-2 and R-5 cases;
  R-9 → the four last lines pasted in the pull request, case count 26 before and 39 after;
  R-10 → `Commit::test_a_rename_source_is_judged_too`;
  R-11 → `Commit::test_unknown_ref_takes_the_narrow_route`, `Commit::test_a_malformed_event_payload_takes_the_narrow_route`, and `Mode` unmodified for the shared predicate.
- Manual / browser / screenshot / eval: none new; the next real tap on `main` after the merge is the
  production observation the intent names (its commit touches both indexes and `gen_index.py --check`
  on it is up to date), and the handoff's task state should record it when it happens.

## Rollback
Revert the commits. The committer returns to staging its fixed list and the allowlist to its former set;
no data, format or workflow changes persist, and no other file imports the new functions.
`scripts/approve_dispatch.py` is not a locked path, so the revert could itself be a delegated item.

## Deviations log (append during implementation; same commit as the deviation)
- 2026-09-14 — step 1 predicted exactly three red cases before the code and found four:
  `test_index_only_changes_do_not_make_a_commit` is red too, because the spec's R-8 acceptance puts the
  "regenerated 1 index file(s)" stdout assertion inside it, and no line is printed before the code
  exists. The plan miscounted; the spec did not change, no case was edited, and the direction is the
  safe one (one more case proven to exercise the change). The other two new cases were green as
  predicted, for the reason predicted. 1 of 5.
- 2026-09-14 — the build commit (98daa7c) edited the signed spec's body, design step 4, which first said
  the regenerated indexes were left staged on the index-only refusal; R-5's own acceptance test requires
  the index to be empty, so the code refuses before staging and the sentence was corrected to match.
  The file list allows a spec body edit "only if the review finds a line the code proves wrong", and the
  code proved it before the review did; the deviation entry written in that commit said "the spec did not
  change", which was wrong about this sentence. Logged here as the plan pass asked. 2 of 5.
