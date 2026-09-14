---
type: sdlc/plan
id: advance-push
title: Fetch, compare, fast-forward, then write; six cases in a new module, five seen red first
description: "delegated_merge.advance() gains a merge_sha keyword and three steps before its dirty check (fetch the checkout's branch, refuse unless the fetched tip is the merge commit, fast-forward with --ff-only), run() passes the merge endpoint's sha; six cases in the new scripts/test_delegated_merge_advance.py on a fixture whose bare remote moves after the checkout, five red before the code; one sentence in knowledge/decisions/run-queue.md."
stage: build
# status: draft | in-review | approved | delegated | superseded  (require-plan.sh refuses code edits until approved)
status: in-review
# kind: feature | fix  (fix: protect-tests.sh refuses edits to existing test files)
kind: fix
reads: spec.md
# approved-by: engineer for routine; tech lead/architect for medium/high risk; set only by a human
approved-by:
approved-on:
risk-class: low
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/55
tags: [delegated-mode, run-queue, delegated-merge, active-pointer, fix]
timestamp: 2026-09-14T05:45:00Z
---
# Plan: the advance fetches and fast-forwards onto the merged main before it writes (from intent.md 2026-09-08)

`kind: fix`: the advance has never landed in production, and the intent files it as a defect. Under `kind: fix`
`protect-tests.sh` locks every *existing* test file, which is also what the spec's R-5 requires of
`scripts/test_delegated_merge.py`; the regression cases go in a new module, the route the hook's own header
names (spec C2, D4, G-6). Step 1 writes the cases and watches them fail before step 2 writes any code.

No engineer interview: the owner is the only human and works from a phone, so the repository's own record
stood in for it (`CLAUDE.md` conventions, the lessons named below, the spec's gotchas G-1 to G-6, and the
three owner answers on the intent).

## Files that change
- scripts/delegated_merge.py — `advance(root, out, merged_slug, number, policy, now=None, merge_sha=None)`: `branch` computed first, then `git fetch origin <branch>` (failure: the `advance commit not pushed (fetch of origin/<branch> failed: <err>); the next merge will advance` note, return `None`), `tip = rev-parse FETCH_HEAD` compared to `merge_sha` when given (mismatch: the `origin/<branch> is at <sha12>, not the merge commit <sha12>; not advancing` note, return `None`), `git merge --ff-only FETCH_HEAD` (failure: the `the checkout could not fast-forward to origin/<branch> (<err>); not advancing` note, return `None`), every new git call `check=False`; the existing flow from the dirty check to the non-forced push unchanged (R-1 to R-4). `run()`: `merged = gh_api("PUT", ...)` kept, `advance(..., now=now, merge_sha=(merged or {}).get("sha"))` (R-6). The docstring of `advance()` gains the three steps; the comment at the rejected push no longer blames a third party for what was the checkout's own age
- scripts/test_delegated_merge_advance.py — new; `import test_delegated_merge as base` for `FIXTURE_POLICY`, `ADVANCE_INTENT`, `ADVANCE_LOG`, `_write`; `class MovingRemote(unittest.TestCase)` with a bare remote, the checkout clone, and a second clone that moves the remote after the checkout was taken; helpers `_git`, `_commit`, `_move_remote(subject) -> sha`, `_remote_tip()`; six cases: `test_the_advance_lands_on_top_of_the_merge` (R-1), `test_a_tip_that_is_not_the_merge_commit_is_a_note` (R-2), `test_a_diverged_checkout_is_a_note_not_a_reset` (R-3), `test_a_push_rejected_after_the_fast_forward_is_a_note` (R-4, a `pre-receive` hook on the bare remote that exits 1 and appends one line to a counter file per attempt), `test_run_passes_the_merge_sha_to_advance` (R-6, `base.Checkout(...).happy_path()`, `dm.main(checkout.argv())` with `dm.advance` replaced by a recorder for the call's duration), `test_no_merge_sha_still_fast_forwards` (R-6)
- knowledge/decisions/run-queue.md — one sentence under `## Consequences`: the advance shipped with a fixture whose remote never moved between the checkout and the push, the one case production never produces, and `advance-push` added the fixture that moves (R-7)
- work/advance-push/plan.md — this plan; its deviations log
- work/advance-push/log.md — one ledger line per gate
- work/advance-push/index.md — regenerated
- work/index.md — regenerated

## Release-gated
(none) — no path under `RELEASE_GATED_PATHS` (`migrations infra terraform helm`) is touched. `scripts/delegated_merge.py`
is under `PLAN_REQUIRED_PATHS` and on `.sdlc/delegation.yaml`'s `locked-paths`, so the pull request is the owner's
click (spec C1); the workflow file, the hooks and `.sdlc/` are not touched.

## Order of work (each step independently verifiable)
1. **The failing cases first.** The new module and its fixture: `setUp` initialises the bare remote, writes the
   three-item tree the existing `Advance` fixture writes (its constants, imported), commits with the fixture's own
   identity (`knowledge/lessons/tests-carry-their-own-environment.md`), pushes, and clones the remote a second
   time; `_move_remote(subject)` commits a marker file in the second clone, pushes it, and returns its sha, so
   the remote's `main` is one commit ahead of the checkout, as the merge API leaves it. All six cases written.
   Predicted red against today's code, five: R-1's (the push is non-fast-forward, `advance` returns `None`,
   the remote tip is the moved commit), R-2's and R-3's (today's code commits locally before its push fails,
   so `HEAD` moves), `test_run_passes_the_merge_sha_to_advance` (the recorder is called without `merge_sha`),
   and `test_no_merge_sha_still_fast_forwards` (the same non-fast-forward push as R-1). Predicted green,
   one: `test_a_push_rejected_after_the_fast_forward_is_a_note`, because today's push is also rejected once
   with a `not pushed` note; it is mutation-tested red in step 2 by making the push a retry loop, the result
   recorded in the pull request. The spec's R-8 says four red; this plan predicts five, and whichever count
   step 1 observes, the other document's line is corrected in the same commit and logged below. Verify:
   `python3 scripts/run_tests.py -p test_delegated_merge_advance.py` shows exactly those failures
   (`knowledge/lessons/a-verifiable-command-fails-before-the-change.md`); `python3 scripts/run_tests.py -p
   test_delegated_merge.py` is untouched and green.
2. **The three steps and the keyword.** In `advance()`: the keyword, `branch` moved to the top, fetch, tip
   comparison, `--ff-only`, each failure its own note and `None`, then the existing flow. Verify: R-1, R-2,
   R-3 and `test_no_merge_sha_still_fast_forwards` green; the existing `Advance` class green unmodified, in
   particular `test_a_failed_push_leaves_the_run_reporting_the_merge`, whose remote does not exist so the fetch
   fails first and the note still reads `not pushed` (spec D3); the R-4 hook case still green and its
   mutation (a retry loop around the push) red, then reverted.
3. **The sha reaches the advance.** In `run()`: keep the merge response, pass `merge_sha`. Verify:
   `test_run_passes_the_merge_sha_to_advance` green; the whole of `test_delegated_merge.py` green,
   `EndToEnd` and `StaleMerge` unmodified.
4. **The decision record.** The one sentence in `knowledge/decisions/run-queue.md`. Verify:
   `grep -c "advance-push" knowledge/decisions/run-queue.md` is at least 1; `python3 scripts/check_okf.py` ends
   `0 warnings`.
5. **Regenerate and verify the whole loop.** `python3 scripts/gen_index.py`, `python3 scripts/gen_context_files.py`,
   `git add` every changed and new file (`knowledge/lessons/stage-new-files-before-verify.md`), `scripts/verify.sh`,
   commit, then `python3 scripts/check_artifact_chain.py --base origin/main --slug advance-push`
   (`knowledge/lessons/commit-before-the-chain-check.md`), `scripts/run_evals.sh`, `python3 scripts/check_okf.py`,
   and the R-5 check: `git diff origin/main --name-only` lists exactly the two code files, the decision record
   and this item's directory, and `git diff origin/main --stat -- scripts/test_delegated_merge.py
   .github/workflows/delegated-merge.yml` prints nothing.
6. **Draft pull request, review, ready.** Already open as #87 on this session's `claude/advance-push` branch,
   with `[advance-push]` in the title and `Work-Item: advance-push` in the body. After step 5: paste the four
   last lines, run `/sdlc-review` with `plan-reviewer` and `security-reviewer` on a model other than the
   writer's, fix what they find with evidence, post the findings with `Important: 0 | Nits: <m>`, then ready.
   The merge script is a locked path, so the owner clicks merge; that merge is the first production run of
   the fetch-and-fast-forward, and the handoff records what its log says.

## Risks
- Risk: the runner's checkout is shallow (`actions/checkout` depth 1), and `git merge --ff-only` on it
  behaves differently from the full clones the fixture uses → mitigation: `git fetch origin <branch>` on a
  shallow clone deepens as needed, and a fast-forward needs only that `HEAD` be an ancestor of the fetched
  tip, which the merge commit's first parent guarantees (spec G-4); the failure mode is a note, not a write,
  and the owner's merge click on this pull request is the production observation.
- Risk: the merge endpoint's `sha` is absent or not the tip the fetch sees (GitHub's response is the merge
  commit, but a push in the same seconds moves `main` past it) → mitigation: `None` skips the comparison
  and still fast-forwards (R-6); a mismatch is a note naming both shas and no write (R-2); the next merge
  advances, as the existing comment already promises.
- Risk: a new git call left `check=True` raises `MergeError` inside `advance()`, which `run()` turns into the
  generic `could not advance` note and hides the specific reason → mitigation: the three new calls are
  `check=False` and write their own notes (spec G-5); the cases assert the specific wording.
- Risk: `unittest`'s loader collects the existing module's classes a second time through the new module's
  import → mitigation: `import test_delegated_merge as base` binds a module, not names, so the loader finds
  no `TestCase` subclass in the new module's namespace but `MovingRemote`; step 1's run of the new module
  alone shows six cases, no more.
- What this could break: the pointer's advance after every delegated merge, which today never lands. A
  defect here surfaces as a note in the merge job's log and an unchanged pointer, the state production is
  already in; nothing before the merge changes (R-5).
- Options considered and not taken: a fresh checkout after the merge, a `git reset --hard`, a rebase or a
  forced push (intent Must-not; the checkout is `main`'s and stays so); retrying the push (`work/run-queue`
  R-3); moving the fetch into the workflow file (a protected path, and the intent puts the change in the
  script); editing `scripts/test_delegated_merge.py` to add the cases beside `Advance` (`kind: fix` locks it,
  and R-5 wants it unmodified as proof nothing before the merge changed); `kind: feature` to unlock it (the
  intent files a defect, and a new module is the designed route).

## Proof
- `scripts/verify.sh` green, ending `VERIFY: PASS (<sha>)`
- Spec rows → tests: R-1 → `MovingRemote::test_the_advance_lands_on_top_of_the_merge`;
  R-2 → `MovingRemote::test_a_tip_that_is_not_the_merge_commit_is_a_note`;
  R-3 → `MovingRemote::test_a_diverged_checkout_is_a_note_not_a_reset`;
  R-4 → `Advance::test_a_failed_push_leaves_the_run_reporting_the_merge` unmodified and
  `MovingRemote::test_a_push_rejected_after_the_fast_forward_is_a_note` (mutation-tested);
  R-5 → `git diff origin/main --name-only` and the `--stat` on the two untouched files, `python3 scripts/run_tests.py` green with every existing class unmodified;
  R-6 → `MovingRemote::test_run_passes_the_merge_sha_to_advance` and `MovingRemote::test_no_merge_sha_still_fast_forwards`;
  R-7 → the grep on `knowledge/decisions/run-queue.md` and `OKF: ... 0 warnings`;
  R-8 → the four last lines pasted in the pull request, the new module's six cases counted and the red set of step 1 recorded.
- Manual / browser / screenshot / eval: none new. The production observation is the next delegated merge
  after this one lands: its job log shows `ADVANCE: .sdlc/active -> <slug>` and `main` gains an advance
  commit whose first parent is the merge commit; the handoff's task state records it when it happens.

## Rollback
Revert the commits. `advance()` returns to committing on the pre-merge checkout and its push to being
rejected on every real merge, which is the state `main` is in today; no data, format, workflow or policy
change persists, and nothing else imports the new module. The revert touches a locked path, so it is the
owner's click too.

## Deviations log (append during implementation; same commit as the deviation)
- 
