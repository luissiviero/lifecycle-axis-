---
type: lesson
title: A verifiable command fails before the change
description: "A check written beside the work it checks tends to pass whether or not the work is there. Twice in work/ci-budget an artifact shipped commands that would have reported success with the change absent: six of a plan's Verifiable clauses, and six unit tests that one of two invocations silently skipped. Watch the command fail first, or it is documentation, not proof."
tags: [lesson, tests, verification, plans, evals]
resource: ../../work/ci-budget/log.md
timestamp: 2026-09-13T15:30:00Z
---
# A verifiable command fails before the change

## What happened
Twice in `work/ci-budget`, two days apart, on different kinds of artifact.

1. The automated reviewer on pull request 70 read the plan's `Verifiable:` clauses and found
   **six commands that would have passed with the work absent** — one shape, caught six times.
   `grep -n "head_repository" .github/workflows/pr-review.yml` finds the string whether the guard
   gates the checkout or merely reports beside it; `check_okf.py` ends `0 warnings` on a tree where
   the decision record was never written. Each clause named a real command and none of them
   discriminated. The plan was re-written to assert the thing that only the change makes true.
2. The M2 revision on pull request 71 found that the two new classes in
   `scripts/test_delegated_merge.py` sat **after** the `if __name__ == "__main__"` block, so
   `python3 scripts/test_delegated_merge.py` ran 39 tests and `python3 -m unittest
   scripts.test_delegated_merge` ran 45. Six new cases were green in one invocation and skipped in
   the other, and the invocation that skipped them still exited 0. The block moved to the end of the
   file; both now run 45.

A correction in the same ledger is the third face of it: a review line claimed every new test had
been proved to fail against the reverted source. M2 checked and about eleven were boundary pins that
pass against `main` — legitimate tests, but not evidence of the kind the line claimed.

## Rule
Run the new command and **watch it fail** before writing the change, then watch it pass. A check you
only ever saw green proves that it is green, not that the work is there. Three cheap habits:

- Write the test, eval case or `Verifiable:` clause first and run it. If it passes on a clean tree,
  it is the wrong clause — sharpen it until the absence of the work makes it red.
- A grep-shaped check is the easiest to fool: the string may already exist. Before trusting one,
  `git stash` the change (or grep `origin/main`) and confirm the case goes red.
- Run a test file **both ways** — `python3 <file>` and `python3 -m unittest <module>` — and compare
  the counts. A difference means some tests are unreachable in one of them.

## Where it is enforced
Prose and review. `scripts/run_tests.py` runs every suite by module, so the full run is not fooled by
a misplaced `if __name__` block, but a direct invocation still is, and the counts are what expose it.
No hook can tell a discriminating command from a decorative one: that judgment is the reviewer's, and
`REVIEW.md`'s memory pass is where it has twice been caught.
