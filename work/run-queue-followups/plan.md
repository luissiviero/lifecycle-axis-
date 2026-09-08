---
type: sdlc/plan
id: run-queue-followups
title: One early refusal in check_artifact_chain.py, its six cases, an eval oracle, and the lesson's enforcement section
description: "A guard after changed_all refuses when the diff is empty, the caller did not ask for the self-check, and the working tree is dirty or unreadable; six regression cases, one mutation-tested eval, and the lesson stops saying the guard is nowhere."
stage: build
status: delegated
kind: feature
reads: spec.md
approved-by: claude
approved-on: 2026-09-08
risk-class: low
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/58
tags: [check-artifact-chain, verify, git, guards, lessons]
timestamp: 2026-09-08T19:20:00Z
---
# Plan: an empty diff on a dirty tree is refused (from intent.md 2026-09-08)

`kind: feature`, not `fix`, and the distinction is load-bearing. `kind: fix` closes `protect-tests.sh`
over existing test files, and this item must add cases to `scripts/test_check_artifact_chain.py`. It is
also the honest label: nothing regressed, the enforcement never existed. The lesson says so in the words
this item deletes — "Where it is enforced / Nowhere yet".

Revised once before implementation (`revisions/1.md`): the guard identifies the self-check by the caller
passing literally `--base HEAD`, not by resolving refs to commits, and it fails closed when `git status`
cannot be read.

## Files that change
- scripts/check_artifact_chain.py — the early refusal after `changed_all`, with the comment recording why its predicate differs from `self_check` at `:571` (R-1, R-2, R-3, R-4, R-5)
- scripts/test_check_artifact_chain.py — new class `DirtyTree` with six cases and a stage-without-commit fixture helper (R-1, R-2, R-3, R-4, R-5, R-6)
- evals/cases/chain-refuses-empty-diff-on-a-dirty-tree.yaml — new; the oracle, both halves, no blank line in its check block (R-8)
- knowledge/lessons/commit-before-the-chain-check.md — the "Where it is enforced" section names the guard, and keeps the rule for the case it cannot reach (R-7)
- work/run-queue-followups/spec.md — signed under the grant, re-signed under revision 1
- work/run-queue-followups/revisions/1.md — new; the consensus record, two `verdict: revise` sections
- work/run-queue-followups/revisions/index.md — new; a revisions directory without one is an OKF warning
- work/run-queue-followups/plan.md — this plan; its deviations log
- work/run-queue-followups/log.md — ledger lines at each gate
- work/run-queue-followups/index.md — regenerated
- work/index.md — regenerated

## Release-gated
(none) — no path under `RELEASE_GATED_PATHS` (`migrations infra terraform helm`) is touched.

## Order of work (each step independently verifiable)
1. **The failing cases first.** Add `DirtyTree` to `scripts/test_check_artifact_chain.py` with a helper
   that builds `_make_repo`'s tree and then stages or writes without committing. Six cases: staged work
   with `--base main` refuses (R-1); the same tree with `--base HEAD` passes (R-2); a clean tree with no
   commits passes (R-3); an untracked file refuses (R-4); an ignored path alone passes (R-4); an
   unreadable `git status` refuses (R-5). Verify: `python3 -m unittest scripts.test_check_artifact_chain -k DirtyTree`
   — the three refusal cases must be **red**, the three pass cases green. A refusal case that is green
   here is not exercising the guard, and the step is not done. This is the step that would have caught
   the design revision 1 corrected, so it is not a formality.
2. **The guard.** After `changed_all` is built at `:536`, refuse when `changed_all` is empty, `a.base`
   is not literally `"HEAD"`, and either `git status --porcelain` failed (R-5) or printed at least one
   line (R-1). One `  FAIL:` line in the Interfaces shape, then `CHAIN: FAIL`, then `sys.exit(1)`. Paths
   taken from column 4, rename entries split on the last ` -> `, each `repr`'d, first three then
   `, +<k> more`. A comment records why this predicate is deliberately not `self_check` (G-8). Verify:
   step 1's six cases green; the full file green; `:570-571` untouched in the diff.
3. **The eval.** Add `evals/cases/chain-refuses-empty-diff-on-a-dirty-tree.yaml` in the shape of
   `chain-allows-intent-only-pr.yaml`: temp repo, own identity, assert exit 1 on the dirty tree and exit 0
   on the same tree once committed. Verify: `scripts/run_evals.sh --only chain-refuses-empty-diff-on-a-dirty-tree`
   passes, then mutation-test it three ways — guard deleted, condition inverted, `--base HEAD` exemption
   removed — and confirm red each time before restoring. An oracle not shown red is not an oracle
   (`knowledge/lessons/eval-checks-have-no-blank-lines.md`).
4. **The lesson.** Rewrite "Where it is enforced" to name the check, the three-part condition and the
   message, and keep the rule for `--base HEAD`, which the guard deliberately does not reach. Verify:
   `grep -c 'Nowhere yet'` is `0`; `python3 scripts/check_okf.py` ends `0 warnings`.
5. **Regenerate and verify the whole loop.** `python3 scripts/gen_index.py`, `python3 scripts/gen_context_files.py`,
   `git add -A`, then `scripts/verify.sh`, then commit, then the chain check against `origin/main`,
   `scripts/run_evals.sh`, `python3 scripts/check_okf.py`. Commit before the `origin/main` chain check,
   never before staging (`knowledge/lessons/stage-new-files-before-verify.md`, and this item's own
   subject — from this commit on, the guard enforces it).

## Risks
- Risk: the guard fires during this item's own verify runs, since the tree is dirty for most of the work
  → mitigation: `scripts/verify.sh` uses `--base HEAD` (`.sdlc/config.env:25`), which R-2 exempts by
  construction; the `--base origin/main` run is done after committing, which is the rule the lesson
  already states. Step 5 orders it that way.
- Risk: an existing test leaves a tree dirty in some way I did not find and starts failing → mitigation:
  G-4 records that every add site in the file commits in the same helper; step 2 runs the full file, so a
  surprise surfaces at the step that caused it.
- Risk: the R-5 fixture cannot actually break `git status` portably, leaving the fail-closed path
  untested → mitigation: if `GIT_INDEX_FILE` pointing at an unreadable path does not produce a non-zero
  exit on this runner, the case is rewritten to drive the guard's helper directly rather than dropped; an
  untested fail-closed path is not acceptable, since it is the security pass's Important finding.
- What this could break: any caller passing a non-`HEAD` base on a dirty tree. G-6 establishes there is
  none in this repository: `verify.sh` uses `--base HEAD`, `sdlc-gate.yml:41` and `deploy.yml:49` run on
  clean CI checkouts.
- Options considered and not taken: **gating the guard on `_rev(a.base) != _rev("HEAD")` — tried, and
  found inert in the recorded scenario, where the base and HEAD are the same commit; reproduced three
  times and corrected in `revisions/1.md`, recorded here so a later reader does not repeat it**;
  appending to `errors` instead of exiting early (D1 — it would print the misleading pointer notes
  first); placing the guard at the mode choice at `:599` (D3 — same problem); a `notes` line only (G-7 —
  leaves `CHAIN: PASS`, reproducing the defect); treating a failed `git status` as a clean tree (D4 —
  fails open in the one place this item exists to close); making the guard fire on `--base HEAD` too
  (contradicts `stage-new-files-before-verify.md` and would break every local verify).

## Proof
- `scripts/verify.sh` green, ending `VERIFY: PASS (<sha>)`
- Spec rows → tests: R-1 → `DirtyTree::test_staged_work_with_an_empty_diff_is_one_clear_failure`;
  R-2 → `DirtyTree::test_self_check_on_a_dirty_tree_still_passes`;
  R-3 → `DirtyTree::test_clean_tree_with_no_commits_still_passes`;
  R-4 → `DirtyTree::test_untracked_file_counts_as_dirty` and `DirtyTree::test_ignored_paths_do_not_count`;
  R-5 → `DirtyTree::test_unreadable_status_refuses`;
  R-6 → the full `test_check_artifact_chain.py` suite green with pre-existing cases unmodified, case count
  before (78) and after stated in the pull request;
  R-7 → `grep -c 'Nowhere yet' knowledge/lessons/commit-before-the-chain-check.md` is `0` and `check_okf.py`
  ends `0 warnings`;
  R-8 → `scripts/run_evals.sh` ends `0 fail` with the new case, plus the three mutation results;
  R-9 → the four last lines pasted in the pull request.
- Manual / browser / screenshot / eval: `evals/cases/chain-refuses-empty-diff-on-a-dirty-tree.yaml`,
  mutation-tested red three ways before being trusted green.

## Rollback
Revert the commit. The guard adds one refusal path; nothing persists, no data or format changes, and no
other file depends on the new behaviour. `check_artifact_chain.py` is on the policy's `locked-paths`, so
the merge is the owner's click and the revert would be too.

## Deviations log (append during implementation; same commit as the deviation)
- 
