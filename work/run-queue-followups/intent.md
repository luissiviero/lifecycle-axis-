---
type: sdlc/intent
id: run-queue-followups
title: The chain check reports PASS on work it never saw; make it say so instead
description: "check_artifact_chain.py diffs <base>...HEAD, so staged and uncommitted work is invisible to it; an empty diff is in-progress mode, and the check prints CHAIN: PASS under a note describing a diff that does not exist. It audited the wrong work twice in one session. The lesson written for it says the guard is nowhere yet; this item writes the guard."
stage: plan
status: in-review
author: Luis Siviero (repo owner), who narrowed this item to its last piece after pull request 57 merged; drafted by Claude from knowledge/lessons/commit-before-the-chain-check.md and the source it cites
approved-by:
approved-on:
risk-class: low
mode: supervised
delegated-by:
delegated-on:
supersedes:
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/56
tags: [check-artifact-chain, verify, git, guards, lessons, followups]
timestamp: 2026-09-08T18:40:00Z
---
# Intent: the chain check reports PASS on work it never saw

## Problem
This item opened carrying three leftovers from `work/run-queue`. Pull request 57 merged two of them:
the `sdlc-run` skill now prints the active slug first and the rest excluding it, and both lessons are
filed with their rule pointers. One is left, and it is the only one that needs code.

`knowledge/lessons/commit-before-the-chain-check.md`, merged in that same pull request, ends by saying
so in its own words:

> ## Where it is enforced
> Nowhere yet. A guard in `check_artifact_chain.py` (refuse, or at least warn, when the diff is empty
> but `git status --porcelain` is not) is a small `scripts/` change that needs a plan; until then this
> lesson is the guard.

A lesson is a guard only for whoever reads it. The mechanism it describes, measured on 2026-09-08:

- `scripts/check_artifact_chain.py:526` lists changed files with `git diff --name-only <base>...HEAD`,
  which sees commits and nothing else. Staged and working-tree changes are not in `HEAD`.
- An empty result is not treated as "nothing to say". `check_artifact_chain.py:540` documents it as the
  in-progress mode that "validates what exists", because `all([])` is `True`. The check then prints
  `CHAIN: PASS` under a note asserting the diff touches only the pointer's item.
- So the failure is silent and confident at once: the note describes a diff that does not exist, and
  the item it names is whatever `.sdlc/active` points at, not the work in the tree.

The lesson records both occurrences, one item apart. A new intent staged but not committed produced a
pass whose note named `work/approve-by-dispatch/`, the previous item. The whole implementation of
`work/run-queue` staged but not committed produced a pass that had checked none of the code.

The neighbouring case is already guarded, which is what makes this one conspicuous. When the base ref is
one git does not know, `check_artifact_chain.py:527-535` refuses with a one-line explanation rather than
reading the empty diff as a pass, added under `work/retire-active-pointer` R-4 for exactly this class of
defect. Here the ref is fine and the diff is honestly empty, so that guard never fires.

## Proposed outcome
- Running the check the way CI runs it, against a tree with staged or uncommitted work and no commits
  behind it, produces a message naming what it could not see, instead of `CHAIN: PASS`. Observable: a
  case in `scripts/test_check_artifact_chain.py` that stages a file, runs the check, and asserts the new
  message and exit status; the same case asserts the message names the uncommitted paths, so a reader
  learns what to do rather than only that something is wrong.
- The self-check keeps working untouched. `scripts/verify.sh` runs the check with `--base HEAD`, whose
  diff is empty by construction, and the normal, correct workflow runs it on a dirty tree: stage every
  new file, verify, then commit (`knowledge/lessons/stage-new-files-before-verify.md`). A guard that
  fails that run would contradict a merged lesson and break every local verify. Observable:
  `scripts/verify.sh` ends `VERIFY: PASS` on a dirty tree, as today.
- Behaviour on a committed tree is unchanged, in both modes. Observable: the existing cases in
  `scripts/test_check_artifact_chain.py` pass unmodified, and CI, which checks out a commit and so is
  never dirty, sees no difference.
- The lesson's "Where it is enforced" section names the guard instead of saying nowhere.
- Everything ends green: `scripts/verify.sh` `VERIFY: PASS`, `check_artifact_chain.py` `CHAIN: PASS`,
  `scripts/run_evals.sh` `0 fail`, `scripts/check_okf.py` `0 warnings`.

## Affected users and systems
- Users: every agent session and every human who runs the chain check locally before committing.
- Services / repos / data: `scripts/check_artifact_chain.py` (the guard) and
  `scripts/test_check_artifact_chain.py` (its regression case); `knowledge/lessons/commit-before-the-chain-check.md`
  (the enforcement section). `scripts/` is in `PLAN_REQUIRED_PATHS`, so the edit needs a signed plan first.

## Constraints
- Must: leave the `--base HEAD` self-check green on a dirty tree. That is not an edge case, it is the
  documented order of work, and `scripts/verify.sh` depends on it.
- Must: distinguish the honest empty diff from the misleading one. A branch with no commits yet and a
  clean tree has nothing to report and must stay quiet; the code already computes whether the base
  resolves to `HEAD`, which the spec may reuse.
- Must: carry a regression test that fails without the guard, in the file that already tests this script.
- Must not: change what the check reports on a committed tree, in either mode, or touch the approval,
  grant, signature, revision or deviation logic.
- Must not: edit `.sdlc/`, `.claude/hooks/`, `.github/workflows/`, `scripts/verify.sh` or `scripts/checks/`.
- Out of scope: the `gh`-absent crash in the same file; making CI run the check on anything but a commit;
  any change to how in-progress mode judges a real diff.

## Risk class
low — one guard in one script, plus its test and a lesson's closing section. It adds a refusal on a case
that today reports success, so the failure mode of getting it wrong is a check that refuses work it
should have passed, caught immediately by `scripts/verify.sh` and by the script's own suite. The same
value is in the `risk-class` key above, and the policy delegates `low`.

One thing the owner should weigh before granting, because it decides where this item goes in the queue:
`scripts/check_artifact_chain.py` is on the `locked-paths` list in `.sdlc/delegation.yaml`, the files
that judge a merge and so must be byte-identical to main's in any delegated pull request. The merge
script will refuse this item's pull request, and the merge is the owner's click. Per the `sdlc-run`
skill, no advance follows a locked-path item and the queue ends there, so this one is granted last.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: refuse or warn? Proposed: refuse (exit 1, `CHAIN: FAIL`) when the base is not `HEAD` and the diff is
  empty and the tree is dirty, which is the run that mirrors CI and the only one that lied; and stay
  silent on the `--base HEAD` self-check, whose empty diff is by construction and whose dirty tree is
  the normal case. The R-4 refusal a few lines above is the precedent for the wording.
  A:
- Q: does the dirtiness test count untracked files, or only staged and modified ones? Proposed: count
  untracked too, since the first occurrence was a new intent file that was untracked at the time, and
  `.gitignore` already keeps the noise out.
  A:
- Q: should the message list the unseen paths, or only say the tree is dirty? Proposed: list them,
  capped at a handful with a count for the rest, because the fix is `git add` and `git commit` on exactly
  those paths.
  A:
