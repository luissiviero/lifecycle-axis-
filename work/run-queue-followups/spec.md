---
type: sdlc/spec
id: run-queue-followups
title: An empty diff on a dirty tree is refused in one line, not reported as PASS
description: "check_artifact_chain.py takes in-progress mode whenever the diff is empty, so staged and uncommitted work reads as CHAIN: PASS under a note describing a diff that does not exist. Refuse that case early, the way the unknown-base-ref case is already refused, and leave verify.sh's --base HEAD self-check untouched."
stage: design
status: delegated
reads: intent.md
approved-by: claude
approved-on: 2026-09-08
skills-applied: [security-standards]
skills-version: a8b7001
prompt: "/sdlc-run run-queue-followups -> /sdlc-spec, in session_01DMnAiTeh543daEAerPicB3, from the approved and delegated intent and an explorer pass over check_artifact_chain.py's diff and mode logic, test_check_artifact_chain.py's fixtures, sdlc-gate.yml, deploy.yml and .sdlc/config.env; revised once (revisions/1.md)"
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/58
tags: [check-artifact-chain, verify, git, guards, lessons]
timestamp: 2026-09-08T19:20:00Z
---
# Spec: an empty diff on a dirty tree is refused in one line

## Requirements (each maps to an intent outcome)
| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R-1 | The check refuses, in one line, when all three hold: the diff against `--base` is empty, the caller did not ask for the self-check (`--base` is not literally `HEAD`), and the working tree has uncommitted changes. The line names the count and a sample of the unseen paths and says what to do. It is an early refusal (`CHAIN: FAIL`, exit 1) in the shape `check_artifact_chain.py:527-535` already uses for an unknown base ref, printed before any other output. The discriminator is call-site identity, not commit identity: in the recorded scenario the base and `HEAD` are the *same* commit, so a revision comparison would leave the guard inert (revision 1). | 1 (a message naming what it could not see, instead of `CHAIN: PASS`) | `scripts/test_check_artifact_chain.py::DirtyTree::test_staged_work_with_an_empty_diff_is_one_clear_failure` — stage a file with no commit behind `--base main`: exit 1, exactly one `  FAIL:` line containing `the diff against 'main' is empty but the working tree is not`, last line `CHAIN: FAIL`. The case must be seen red against the un-guarded build before the guard is written; a case that is green before the guard is not exercising it. |
| R-2 | The self-check is untouched. `--base HEAD` never triggers R-1, whatever the tree's state, because its diff is empty by construction and the documented order of work is stage, verify, commit (`knowledge/lessons/stage-new-files-before-verify.md`). This is the case `scripts/verify.sh` runs through `VERIFY_CMDS` (`.sdlc/config.env:25`). | 2 (`scripts/verify.sh` ends `VERIFY: PASS` on a dirty tree, as today) | `DirtyTree::test_self_check_on_a_dirty_tree_still_passes` — same staged fixture, `--base HEAD`: exit 0, last line `CHAIN: PASS`, no `FAIL` line; and `scripts/verify.sh` run with this spec staged but uncommitted ends `VERIFY: PASS` |
| R-3 | An honest empty diff still passes. A clean tree with no commits beyond the base has nothing to report and must stay quiet: no new line, no failure. | 2 (behaviour on a committed tree unchanged) | `DirtyTree::test_clean_tree_with_no_commits_still_passes` — `_make_repo` then `--base main` with nothing modified: exit 0, last line `CHAIN: PASS`, no `  FAIL:` line |
| R-4 | Untracked files count as uncommitted. The first of the two recorded occurrences was a new `intent.md` that was untracked at the time, so a guard that only saw staged and modified files would have missed it. Ignored paths do not count: `git status --porcelain` excludes them, and `.gitignore` already covers `verify.sh`'s own scratch output (`.sdlc/.last-verify`, `evals/.last-*.json`). | 1 | `DirtyTree::test_untracked_file_counts_as_dirty` — write a file without `git add`, `--base main`: exit 1, one `  FAIL:` line naming the file; `DirtyTree::test_ignored_paths_do_not_count` — write `.sdlc/.last-verify` only: exit 0, `CHAIN: PASS` |
| R-5 | The guard fails closed. If `git status` itself fails, the check cannot determine whether the tree is dirty, and so cannot claim to have examined it: it refuses in the same one-line shape rather than assuming a clean tree. Assuming clean would reopen the exact defect class this item closes, and would contradict `:527-535`, which already treats "git cannot answer" as `CHAIN: FAIL` (revision 1, security pass). | 1 | `DirtyTree::test_unreadable_status_refuses` — invoke with a broken git environment (`GIT_INDEX_FILE` pointing at an unreadable path) so `git status` exits non-zero: exit 1, one `  FAIL:` line naming that the tree's state could not be read, last line `CHAIN: FAIL` |
| R-6 | Behaviour on a committed tree is unchanged in both modes, and every pre-existing case in the suite passes unmodified. The guard is reachable only through a local run: CI checks the chain out fresh and runs the check before `verify.sh` (`sdlc-gate.yml:41` then the Verify step; `deploy.yml:49` likewise), so the tree is always clean there. | 3 (CI sees no difference) | `python3 scripts/run_tests.py` green with the pre-existing `test_check_artifact_chain.py` cases unmodified; the case count before (78) and after is stated in the pull request |
| R-7 | The lesson's closing section names the guard instead of saying nowhere. `knowledge/lessons/commit-before-the-chain-check.md:30-33` currently reads "Where it is enforced / Nowhere yet"; it is rewritten to name the check, the condition and the message, and to keep the rule for the case the guard cannot reach (`--base HEAD`). | 4 (the lesson's enforcement section is true) | `grep -c 'Nowhere yet' knowledge/lessons/commit-before-the-chain-check.md` is `0`; `python3 scripts/check_okf.py` ends `0 warnings`; the file still parses as `type: lesson` |
| R-8 | A new eval oracle watches the guard, and is shown to fail before it is trusted to pass. It follows the shape of `evals/cases/chain-allows-intent-only-pr.yaml`: a temp repo, its own git identity, both halves asserted (refuses dirty, passes clean). Its `check:` block contains no blank line (`knowledge/lessons/eval-checks-have-no-blank-lines.md`). | 1, 3 | `scripts/run_evals.sh` ends `0 fail` with the new case counted; the case is mutation-tested three ways (guard removed, condition inverted, `--base HEAD` exempted) and reported red each time in the pull request |
| R-9 | The whole loop is green: `scripts/verify.sh` ends `VERIFY: PASS`, the chain check ends `CHAIN: PASS`, `scripts/run_evals.sh` ends `0 fail`, `check_okf.py` ends `0 warnings`, and both generators report up to date. | 3 | the last lines, pasted in the pull request |

## Design
### Architecture / data flow
Nothing new flows. One reader of existing state gains one refusal.

`main()` computes the changed-file list at `check_artifact_chain.py:526-536`, then chooses its mode at
`:599` with `in_progress = all(own_artifact(p) for p in changed_all)`. `all([])` is `True`, so an empty
`changed_all` silently selects in-progress mode and the note printed at `:601-604` describes a diff that
does not exist.

The guard goes immediately after `changed_all` is built at `:536`, before the `if active_now:` block at
`:554`. At that point `a.base`, `changed_all` and `ROOT` are in scope, and no rev resolution is needed:
the self-check is identified by the caller passing literally `--base HEAD`, not by comparing commits
(revision 1). `check_artifact_chain.py:570-571` is left untouched.

### Interfaces (APIs, events, schemas) — exact shapes
- R-1 line, the whole of what the check prints for this case:
  `  FAIL: the diff against '<base>' is empty but the working tree is not: <n> uncommitted path(s) (<sample>); the chain check reads commits only, so it would report on nothing -- commit them first, or pass --base HEAD for a local self-check`
  followed by `CHAIN: FAIL`, exit 1, before any other output.
- R-5 line, when `git status` cannot be read:
  `  FAIL: cannot tell whether the working tree is clean (git status failed: <last line of git's stderr>); the chain check will not report on a tree it could not examine -- fix the checkout, or pass --base HEAD for a local self-check`
  followed by `CHAIN: FAIL`, exit 1.
- `<n>` is the number of lines `git status --porcelain` printed. `<sample>` is the first three paths,
  comma-separated, with `, +<k> more` appended when more remain.
- A path is taken from column 4 onward of each porcelain line, and for a rename or copy (status code
  starting `R` or `C`, rendered `R  old.txt -> new.txt`) the part after the last ` -> ` is used, so the
  sample holds a path rather than a combined descriptor (revision 1, nit).
- Each path is `repr`'d so a newline, quote or escape inside a filename stays on one line
  (security-standards §3: the value is untrusted input that reaches an operator's terminal). Git itself
  pre-escapes control characters in porcelain output, so this is the second of two layers.
- No new flag, environment variable, file, status word, front-matter key or workflow input.

### Data and migrations
None. The guard reads the working tree and writes nothing. No field is added, so no data
classification applies (security-standards §4: n/a, no new field).

### Failure modes and how they surface
- **The guard fires where it should not.** The only invocation that legitimately sees an empty diff on a
  dirty tree is `--base HEAD`, which R-2 exempts by construction and pins with a test. CI cannot reach the
  guard at all (R-6). A third-party caller passing a non-`HEAD` base on a dirty tree would now fail; the
  repository has no such caller (G-6).
- **The guard fails to fire.** Caught by R-1's case, which must be seen red before the guard exists, and
  by the eval, which is mutation-tested red three ways (R-8). This is not hypothetical: the design as
  first signed was inert in its own motivating case, and only reproducing the scenario caught it
  (revision 1). A guard appended to `notes` rather than refused early would print a line and still end
  `CHAIN: PASS`, reproducing the very defect (G-7).
- **`git status` itself fails.** Refuses (R-5). The check cannot say what it examined, so it says so.

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: the change makes a command that passes today fail tomorrow, on a working tree rather than on
  committed content — policy: none (a local developer-experience change) — contradiction? no — owner:
  luissiviero — resolution: accepted as the point of the item; the failure is local only (R-6), the
  message names the fix, and `--base HEAD` is exempt so no scripted path changes behaviour.
- C2: `scripts/check_artifact_chain.py` is on `.sdlc/delegation.yaml`'s `locked-paths`, so the
  delegated merge script refuses this item's pull request and the queue ends at it — policy:
  `.sdlc/delegation.yaml` — contradiction? no — owner: luissiviero — resolution: expected and stated in
  the intent; the merge is the owner's click.
- C3: the self-check is recognised by one spelling, the literal `HEAD`. A future caller asking for a
  self-check as `--base @`, as a sha, or as `refs/heads/main` would not be recognised and would meet the
  guard — policy: `knowledge/lessons/one-path-spelling-in-guards.md` — contradiction? no — owner:
  luissiviero — resolution: accepted; the caller set is closed and enumerated (G-6), and the failure
  direction is a refusal the caller can see and fix, not a silent allow. The silent allow is what the
  rejected revision-comparison design produced (revision 1).

## Open questions carried from intent.md
- Refuse or warn? **Resolved as refuse**, and only when the caller did not ask for the self-check
  (R-1, R-2). A note would leave `CHAIN: PASS` standing and reproduce the defect (G-7).
- Untracked, or only staged and modified? **Resolved as untracked too** (R-4), because the first recorded
  occurrence was an untracked file; ignored paths stay excluded.
- List the paths, or only say the tree is dirty? **Resolved as list them**, capped at three with a count
  for the rest, because the fix is `git add` and `git commit` on exactly those paths (Interfaces).

## Decisions (ADR-style: context → decision → consequences)
- D1: **Early refusal, not an accumulated error.** Context: `errors` prints `  FAIL:` lines at `:813` and
  flips the verdict at `:814`, while `notes` never affects the exit code. Decision: use the early-exit
  shape of `:527-535` — one line, `CHAIN: FAIL`, `sys.exit(1)` — rather than `errors.append`. Consequence:
  the output is one line instead of a report computed from a diff known to be wrong; the precedent for
  "the diff answers the wrong question" is followed exactly.
- D2: **The guard asks which call site it serves, not which commit the base names.** Context: the first
  signed design compared `_rev(a.base)` with `_rev("HEAD")`, and in the recorded scenario those are the
  same commit, so the guard was inert in its only motivating case (revision 1, reproduced three times).
  Decision: identify the self-check by the caller passing literally `--base HEAD`. Consequence: no `_rev`
  helper, `:570-571` untouched, one plan step and one risk removed, and the diff shrinks. Over-normalising
  a ref to a commit erased the distinction the guard needed;
  `knowledge/lessons/one-path-spelling-in-guards.md` argues for the literal here, not against it, because
  the failure direction of the literal is a visible refusal and the failure direction of the comparison
  was a silent allow.
- D3: **The guard is placed after `changed_all`, not at the mode choice at `:599`.** Context: `:599` is
  after the `if active_now:` block, so a guard there would run after the pointer checks have already
  emitted notes about a diff that does not exist. Decision: refuse at `:536`, before any of that.
  Consequence: the misleading pointer notes are never printed in this case.
- D4: **A failed `git status` refuses.** Context: the first signed design treated it as "not dirty".
  Decision: fail closed (R-5). Consequence: a broken checkout cannot produce a `CHAIN: PASS` on a tree
  nothing examined, which is the defect class this item exists to close.

## Gotchas found while reading the codebase
- G-1: `self_check` (`:571`) and its `rev` lambda (`:570`) live inside `if active_now:` (`:554-592`).
  With `.sdlc/active` empty they are never defined, so nothing outside that block may reference them.
  This item no longer needs to: D2 removed the reason.
- G-2: CI cannot reach the guard. `sdlc-gate.yml:41` runs the chain check on a fresh `actions/checkout`
  and only then runs `verify.sh`; `deploy.yml:49` is the same shape. The tree is clean at both points.
- G-3: `git status --porcelain` lists untracked files as `??` but omits ignored ones, and `.gitignore`
  already covers `.sdlc/.last-verify`, `evals/.last-*.json`, `__pycache__/` and `monitoring/series/`, so
  a verify run cannot make its own tree look dirty to the guard.
- G-4: no existing test in `test_check_artifact_chain.py` leaves files staged without committing. The
  `_commit` helper (`:30-32`) does `add -A` and `commit` together, and both other add sites do the same,
  so the case this item guards has never been exercised and needs a new fixture variant.
- G-5: tests invoke the script as a subprocess (`:81-85`) against a fresh `git init` temp repo and supply
  identity per commit with `-c user.email=t@t -c user.name=t`, never from ambient config
  (`knowledge/lessons/tests-carry-their-own-environment.md`).
- G-6: the only three callers are `.sdlc/config.env:25` (`--base HEAD`, through `verify.sh`),
  `sdlc-gate.yml:41` and `deploy.yml:49` (both `origin/<ref>` on clean CI checkouts), plus the argparse
  default `origin/main` at `:476`. `delegated_merge.py:48` imports the module and never touches `--base`.
  No caller passes a non-`HEAD` base on a tree that could be dirty.
- G-7: a `notes.append` guard would print its line and still end `CHAIN: PASS` (`:812-815`), reproducing
  the defect it was written to fix. Only `errors` or an early exit changes the verdict.
- G-8: after this item the file holds **two deliberately different** "is this a self-check" predicates:
  the guard's literal `a.base != "HEAD"` (call-site identity: did the caller ask to validate the working
  tree as it stands) and `self_check` at `:571` (commit identity: is there a "before" to judge the
  pointer's retirement against). They answer different questions and must not be unified; doing so
  reintroduces the inertness revision 1 removed. Both carry a comment saying so.

## Not doing
- The `gh`-absent crash in the same file. Separate defect, separate item.
- Making CI run the check against anything but a commit. CI is already correct here (G-2).
- Any change to how in-progress mode judges a diff that is genuinely non-empty. In particular the guard
  does not fire on a dirty tree when the diff is non-empty, though the staged part is still unseen: both
  reviewers agreed that reaches beyond R-1 and would fire during ordinary iterative work.
- Fixing `work/run-queue/log.md:21`'s sha, found during this item's review. It belongs to another work
  item, and editing it here would take the pull request out of in-progress mode.
- Adding the eval-blank-line lesson to `knowledge/lessons/index.md`, which #55 left out. Same reason:
  it is not this item's file.
