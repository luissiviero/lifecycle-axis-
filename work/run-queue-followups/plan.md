---
type: sdlc/plan
id: run-queue-followups
title: One early refusal in check_artifact_chain.py, its four cases, an eval oracle, and the lesson's enforcement section
description: "A guard after changed_all refuses when the diff is empty, the base is not HEAD and the working tree is dirty; _rev is hoisted so the base-versus-HEAD comparison has one spelling; four regression cases, one mutation-tested eval, and the lesson stops saying the guard is nowhere."
stage: build
status: delegated
kind: feature
reads: spec.md
approved-by: claude
approved-on: 2026-09-08
risk-class: low
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/56
tags: [check-artifact-chain, verify, git, guards, lessons]
timestamp: 2026-09-08T19:10:00Z
---
# Plan: an empty diff on a dirty tree is refused (from intent.md 2026-09-08)

`kind: feature`, not `fix`, and the distinction is load-bearing. `kind: fix` closes `protect-tests.sh`
over existing test files, and this item must add cases to `scripts/test_check_artifact_chain.py`. It is
also the honest label: nothing regressed, the enforcement never existed. The lesson says so in the words
this item deletes — "Where it is enforced / Nowhere yet".

## Files that change
- scripts/check_artifact_chain.py — the `_rev` helper at module level, the early refusal after `changed_all`, and `:570-571` switched to the helper (R-1, R-2, R-3, R-4)
- scripts/test_check_artifact_chain.py — new class `DirtyTree` with five cases and a stage-without-commit fixture helper (R-1, R-2, R-3, R-4, R-5)
- evals/cases/chain-refuses-empty-diff-on-a-dirty-tree.yaml — new; the oracle, both halves, no blank line in its check block (R-7)
- knowledge/lessons/commit-before-the-chain-check.md — the "Where it is enforced" section names the guard, and keeps the rule for the case it cannot reach (R-6)
- work/run-queue-followups/spec.md — signed under the grant, in this pull request
- work/run-queue-followups/plan.md — this plan; its deviations log
- work/run-queue-followups/log.md — ledger lines at each gate
- work/run-queue-followups/index.md — regenerated
- work/index.md — regenerated

## Release-gated
(none) — no path under `RELEASE_GATED_PATHS` (`migrations infra terraform helm`) is touched.

## Order of work (each step independently verifiable)
1. **The failing cases first.** Add `DirtyTree` to `scripts/test_check_artifact_chain.py` with a helper
   that builds `_make_repo`'s tree and then stages or writes without committing. Five cases: staged work
   with `--base main` refuses (R-1); the same tree with `--base HEAD` passes (R-2); a clean tree with no
   commits passes (R-3); an untracked file refuses (R-4); an ignored path alone passes (R-4). Verify:
   `python3 -m unittest scripts.test_check_artifact_chain -k DirtyTree` — the three refusal cases fail,
   the two pass cases already pass. A refusal case that passes here means the case is not testing the
   guard, and the step is not done.
2. **The helper.** Add module-level `_rev(ref)` returning the resolved commit or `""`. Replace the
   `rev` lambda at `:570` and point `:571` at the helper. Verify: the whole file's suite still green
   (`python3 -m unittest scripts.test_check_artifact_chain`), proving the `self_check` behaviour that
   `retire-active-pointer` R-2 pinned is unchanged.
3. **The guard.** After `changed_all` is built at `:536`, refuse when `changed_all` is empty, `_rev(a.base)`
   differs from `_rev("HEAD")` (both non-empty), and `git status --porcelain` printed at least one line.
   One `  FAIL:` line in the Interfaces shape, then `CHAIN: FAIL`, then `sys.exit(1)`. Paths `repr`'d,
   first three then `, +<k> more`. A `git status` that fails is treated as not dirty. Verify: step 1's
   five cases green; the full suite green.
4. **The eval.** Add `evals/cases/chain-refuses-empty-diff-on-a-dirty-tree.yaml` in the shape of
   `chain-allows-intent-only-pr.yaml`: temp repo, own identity, assert exit 1 on the dirty tree and exit 0
   on the same tree once committed. Verify: `scripts/run_evals.sh --only chain-refuses-empty-diff-on-a-dirty-tree`
   passes, then mutation-test it three ways — guard deleted, condition inverted, `--base HEAD` exemption
   removed — and confirm red each time before restoring. An oracle not shown red is not an oracle
   (`knowledge/lessons/eval-checks-have-no-blank-lines.md`).
5. **The lesson.** Rewrite "Where it is enforced" to name the check, the three-part condition and the
   message, and keep the rule for `--base HEAD`, which the guard deliberately does not reach. Verify:
   `grep -c 'Nowhere yet'` is `0`; `python3 scripts/check_okf.py` ends `0 warnings`.
6. **Regenerate and verify the whole loop.** `python3 scripts/gen_index.py`, `python3 scripts/gen_context_files.py`,
   `git add -A`, then `scripts/verify.sh`, the chain check against `origin/main`, `scripts/run_evals.sh`,
   `python3 scripts/check_okf.py`. Commit before the chain check, never before staging
   (`knowledge/lessons/stage-new-files-before-verify.md`, and this item's own subject).

## Risks
- Risk: the guard fires during this item's own verify runs, since the tree is dirty for most of the work
  → mitigation: `scripts/verify.sh` uses `--base HEAD` (`.sdlc/config.env:25`), which R-2 exempts by
  construction; the `--base origin/main` run is done after committing, which is the rule the lesson
  already states. Step 6 orders it that way.
- Risk: hoisting `_rev` changes `self_check`'s behaviour and silently reopens the stale-pointer cases
  `retire-active-pointer` R-2 fixed → mitigation: step 2 is a separate, independently verified step whose
  whole proof is that the existing suite stays green; the helper returns the same string the lambda did.
- Risk: an existing test leaves a tree dirty in some way I did not find and starts failing → mitigation:
  G-4 records that every add site in the file commits in the same helper; step 2 and step 3 each run the
  full file, so a surprise surfaces at the step that caused it rather than at the end.
- Risk: `git status --porcelain` is slow or fails in an odd checkout → mitigation: it runs once, only on
  the already-empty-diff path, and a non-zero return is treated as not dirty, so the guard can never
  invent a failure from a broken subprocess.
- What this could break: any caller passing a non-`HEAD` base on a dirty tree. G-6 establishes there is
  none in this repository: `verify.sh` uses `--base HEAD`, `sdlc-gate.yml:41` and `deploy.yml:49` run on
  clean CI checkouts.
- Options considered and not taken: appending to `errors` instead of exiting early (D1 — it would print
  the misleading pointer notes first); placing the guard at the mode choice at `:599` (D3 — same problem);
  a `notes` line only (G-7 — leaves `CHAIN: PASS`, reproducing the defect); making the guard fire on
  `--base HEAD` too (contradicts `stage-new-files-before-verify.md` and would break every local verify).

## Proof
- `scripts/verify.sh` green, ending `VERIFY: PASS (<sha>)`
- Spec rows → tests: R-1 → `DirtyTree::test_staged_work_with_an_empty_diff_is_one_clear_failure`;
  R-2 → `DirtyTree::test_self_check_on_a_dirty_tree_still_passes`;
  R-3 → `DirtyTree::test_clean_tree_with_no_commits_still_passes`;
  R-4 → `DirtyTree::test_untracked_file_counts_as_dirty` and `DirtyTree::test_ignored_paths_do_not_count`;
  R-5 → the full `test_check_artifact_chain.py` suite green with pre-existing cases unmodified, case count
  before and after stated in the pull request;
  R-6 → `grep -c 'Nowhere yet' knowledge/lessons/commit-before-the-chain-check.md` is `0` and `check_okf.py`
  ends `0 warnings`;
  R-7 → `scripts/run_evals.sh` ends `0 fail` with the new case, plus the three mutation results;
  R-8 → the four last lines pasted in the pull request.
- Manual / browser / screenshot / eval: `evals/cases/chain-refuses-empty-diff-on-a-dirty-tree.yaml`,
  mutation-tested red three ways before being trusted green.

## Rollback
Revert the commit. The guard adds one refusal path and one helper; nothing persists, no data or format
changes, and no other file depends on the new behaviour. `check_artifact_chain.py` is on the policy's
`locked-paths`, so the merge is the owner's click and the revert would be too.

## Deviations log (append during implementation; same commit as the deviation)
- 
