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

1. The M1 revision on pull request 70 read the plan's `Verifiable:` clauses and found **six
   commands that would have passed with the work absent or wrong** — one shape, caught six times
   (`work/ci-budget/log.md`, `acf5530`). Two of them: a `grep` for `triage` in
   `docs/sdlc/github-setup.md` matched text already on line 89 of that file, so it would have
   passed before the bullet was written; and the adopter render clause ran `wc -l`, which proves
   the context file is still at the cap and says nothing about whether the new bullet is in it.
   The others were an eval case matching a string already present, two added invariants with no
   test at all, a step citing a test suite the workflow does not invoke, and a fixture literal
   given to the wrong precision. Each clause named a real command and none of them discriminated.
   The plan was re-written to assert what only the change makes true. (The rule-7 request — that
   this shape become a lesson — came separately, from the automated reviewer on the same pull
   request.)
2. The M2 revision on pull request 71 found that the two new classes in
   `scripts/test_check_workflow_permissions.py` sat **after** the `if __name__ == "__main__"` block,
   so `python3 scripts/test_check_workflow_permissions.py` ran 39 tests and `python3 -m unittest
   scripts.test_check_workflow_permissions` ran 45. Six new cases were green in one invocation and
   skipped in the other, and the invocation that skipped them still exited 0. The block moved to the
   end of the file; both now run 45.

This lesson needed correcting twice, on its own evidence, before it was merged — which is left in
the record on purpose, because it is the best argument the lesson has. Its first draft named the
wrong file in instance 2 (`scripts/test_delegated_merge.py`, which never had the defect); the
conformance review on pull request 72 caught that by checking out `441da35` and running both
invocations. Its second draft still described instance 1 with two examples that were never among
the six; the M4 revision caught that by reading the ledger line the paragraph was summarising and
diffing the plan's own history. Both times the author had written from memory of a ledger entry
instead of opening it. A citation is a verifiable command too, and an unrun one is a guess.

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
