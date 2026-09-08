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
prompt: "/sdlc-run run-queue-followups -> /sdlc-spec, in session_01DMnAiTeh543daEAerPicB3, from the approved and delegated intent and an explorer pass over check_artifact_chain.py's diff and mode logic, test_check_artifact_chain.py's fixtures, sdlc-gate.yml, deploy.yml and .sdlc/config.env"
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/56
tags: [check-artifact-chain, verify, git, guards, lessons]
timestamp: 2026-09-08T19:05:00Z
---
# Spec: an empty diff on a dirty tree is refused in one line

## Requirements (each maps to an intent outcome)
| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R-1 | The check refuses, in one line, when all three hold: the diff against `--base` is empty, `--base` resolves to a different commit than `HEAD`, and the working tree has uncommitted changes. The line names the count and a sample of the unseen paths and says what to do. It is an early refusal (`CHAIN: FAIL`, exit 1) in the shape `check_artifact_chain.py:527-535` already uses for an unknown base ref, printed before any other output. | 1 (a message naming what it could not see, instead of `CHAIN: PASS`) | `scripts/test_check_artifact_chain.py::DirtyTree::test_staged_work_with_an_empty_diff_is_one_clear_failure` — stage a file with no commit behind `--base main`: exit 1, exactly one `  FAIL:` line containing `the diff against 'main' is empty but the working tree is not`, last line `CHAIN: FAIL` |
| R-2 | The self-check is untouched. `--base HEAD` never triggers R-1, whatever the tree's state, because its diff is empty by construction and the documented order of work is stage, verify, commit (`knowledge/lessons/stage-new-files-before-verify.md`). This is the case `scripts/verify.sh` runs through `VERIFY_CMDS` (`.sdlc/config.env:25`). | 2 (`scripts/verify.sh` ends `VERIFY: PASS` on a dirty tree, as today) | `DirtyTree::test_self_check_on_a_dirty_tree_still_passes` — same staged fixture, `--base HEAD`: exit 0, last line `CHAIN: PASS`, no `FAIL` line; and `scripts/verify.sh` run with this spec staged but uncommitted ends `VERIFY: PASS` |
| R-3 | An honest empty diff still passes. A clean tree with no commits beyond the base has nothing to report and must stay quiet: no new line, no failure. | 2 (behaviour on a committed tree unchanged) | `DirtyTree::test_clean_tree_with_no_commits_still_passes` — `_make_repo` then `--base main` with nothing modified: exit 0, last line `CHAIN: PASS`, no `  FAIL:` line |
| R-4 | Untracked files count as uncommitted. The first of the two recorded occurrences was a new `intent.md` that was untracked at the time, so a guard that only saw staged and modified files would have missed it. Ignored paths do not count: `git status --porcelain` excludes them, and `.gitignore` already covers `verify.sh`'s own scratch output (`.sdlc/.last-verify`, `evals/.last-*.json`). | 1 | `DirtyTree::test_untracked_file_counts_as_dirty` — write a file without `git add`, `--base main`: exit 1, one `  FAIL:` line naming the file; `DirtyTree::test_ignored_paths_do_not_count` — write `.sdlc/.last-verify` only: exit 0, `CHAIN: PASS` |
| R-5 | Behaviour on a committed tree is unchanged in both modes, and every pre-existing case in the suite passes unmodified. The guard is reachable only through a local run: CI checks the chain out fresh and runs the check before `verify.sh` (`sdlc-gate.yml:41` then the Verify step; `deploy.yml:49` likewise), so the tree is always clean there. | 3 (CI sees no difference) | `python3 scripts/run_tests.py` green with the pre-existing `test_check_artifact_chain.py` cases unmodified; the case count before and after is stated in the pull request |
| R-6 | The lesson's closing section names the guard instead of saying nowhere. `knowledge/lessons/commit-before-the-chain-check.md:30-33` currently reads "Where it is enforced / Nowhere yet"; it is rewritten to name the check, the condition and the message, and to keep the rule for the case the guard cannot reach (`--base HEAD`). | 4 (the lesson's enforcement section is true) | `grep -c 'Nowhere yet' knowledge/lessons/commit-before-the-chain-check.md` is `0`; `python3 scripts/check_okf.py` ends `0 warnings`; the file still parses as `type: lesson` |
| R-7 | A new eval oracle watches the guard, and is shown to fail before it is trusted to pass. It follows the shape of `evals/cases/chain-allows-intent-only-pr.yaml`: a temp repo, its own git identity, both halves asserted (refuses dirty, passes clean). Its `check:` block contains no blank line (`knowledge/lessons/eval-checks-have-no-blank-lines.md`). | 1, 3 | `scripts/run_evals.sh` ends `0 fail` with the new case counted; the case is mutation-tested three ways (guard removed, condition inverted, `--base HEAD` exempted) and reported red each time in the pull request |
| R-8 | The whole loop is green: `scripts/verify.sh` ends `VERIFY: PASS`, the chain check ends `CHAIN: PASS`, `scripts/run_evals.sh` ends `0 fail`, `check_okf.py` ends `0 warnings`, and both generators report up to date. | 3 | the last lines, pasted in the pull request |

## Design
### Architecture / data flow
Nothing new flows. One reader of existing state gains one refusal.

`main()` computes the changed-file list at `check_artifact_chain.py:526-536`, then chooses its mode at
`:599` with `in_progress = all(own_artifact(p) for p in changed_all)`. `all([])` is `True`, so an empty
`changed_all` silently selects in-progress mode and the note printed at `:601-604` describes a diff that
does not exist.

The guard goes immediately after `changed_all` is built at `:536`, before the `if active_now:` block at
`:554`. At that point `a.base`, `changed_all` and `ROOT` are in scope. It runs `git status --porcelain`
once, and refuses when the diff is empty, the base is not `HEAD`, and the output is non-empty.

One supporting change: `self_check` at `:571` is currently a lambda assigned inside the `if active_now:`
block, so it does not exist when `.sdlc/active` is empty and cannot be reused by a guard placed earlier
(G-1). The lambda is replaced by a module-level `_rev(ref)` helper used by both the guard and `:571`.

### Interfaces (APIs, events, schemas) — exact shapes
- R-1 line, the whole of what the check prints for this case:
  `  FAIL: the diff against '<base>' is empty but the working tree is not: <n> uncommitted path(s) (<sample>); the chain check reads commits only, so it would report on nothing -- commit them first, or pass --base HEAD for a local self-check`
  followed by `CHAIN: FAIL`, exit 1, before any other output.
- `<n>` is the number of lines `git status --porcelain` printed. `<sample>` is the first three paths,
  comma-separated, with `, +<k> more` appended when more remain. Paths are taken from column 4 onward of
  each porcelain line, and each is `repr`'d so a newline or a quote inside a filename stays on one line
  (security-standards §3: the value is untrusted input that reaches an operator's terminal).
- `_rev(ref)` -> `str`: the commit `ref` resolves to, or `""` when git cannot resolve it. Two unresolvable
  refs must not compare equal, so an empty result on either side means "not a self-check".
- No new flag, environment variable, file, status word, front-matter key or workflow input.

### Data and migrations
None. The guard reads the working tree and writes nothing. No field is added, so no data
classification applies (security-standards §4: n/a, no new field).

### Failure modes and how they surface
- **The guard fires where it should not.** The only invocation that legitimately sees an empty diff on a
  dirty tree is `--base HEAD`, which R-2 exempts by construction and pins with a test. CI cannot reach the
  guard at all (R-5). A third-party caller passing a non-`HEAD` base on a dirty tree would now fail; the
  repository has no such caller (G-6).
- **The guard fails to fire.** Caught by R-1's case and by the eval, which is mutation-tested red three
  ways before it is trusted (R-7). A guard appended to `notes` rather than refused early would print a
  line and still end `CHAIN: PASS`, reproducing the very defect (G-7); the early-exit shape makes that
  mistake impossible to write by accident.
- **`git status` itself fails.** Treated as "not dirty": the guard declines to refuse rather than
  inventing a failure from a broken subprocess, matching how `_rev` returns `""` rather than raising.

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: the change makes a command that passes today fail tomorrow, on a working tree rather than on
  committed content — policy: none (a local developer-experience change) — contradiction? no — owner:
  luissiviero — resolution: accepted as the point of the item; the failure is local only (R-5), the
  message names the fix, and `--base HEAD` is exempt so no scripted path changes behaviour.
- C2: `scripts/check_artifact_chain.py` is on `.sdlc/delegation.yaml`'s `locked-paths`, so the
  delegated merge script refuses this item's pull request and the queue ends at it — policy:
  `.sdlc/delegation.yaml` — contradiction? no — owner: luissiviero — resolution: expected and stated in
  the intent; the merge is the owner's click.

## Open questions carried from intent.md
- Refuse or warn? **Resolved as refuse**, and only when the base is not `HEAD` (R-1, R-2). A note would
  leave `CHAIN: PASS` standing and reproduce the defect (G-7).
- Untracked, or only staged and modified? **Resolved as untracked too** (R-4), because the first recorded
  occurrence was an untracked file; ignored paths stay excluded.
- List the paths, or only say the tree is dirty? **Resolved as list them**, capped at three with a count
  for the rest, because the fix is `git add` and `git commit` on exactly those paths (Interfaces).

## Decisions (ADR-style: context → decision → consequences)
- D1: **Early refusal, not an accumulated error.** Context: `errors` prints `  FAIL:` lines at `:813` and
  flips the verdict at `:814`, while `notes` never affects the exit code. Decision: use the early-exit
  shape of `:527-535` — one line, `CHAIN: FAIL`, `sys.exit(1)` — rather than `errors.append`. Consequence:
  the output is one line instead of a report that would be computed from a diff known to be wrong; the
  precedent for "the diff answers the wrong question" is followed exactly.
- D2: **`_rev` hoisted to module level.** Context: `self_check` is a lambda defined inside `if active_now:`
  (G-1), so a guard placed before that block cannot use it. Decision: add a module-level `_rev(ref)` and
  have both the guard and `:571` call it. Consequence: one existing line changes and one lambda
  assignment disappears; the base-versus-`HEAD` comparison has one spelling in the file, which is what
  `knowledge/lessons/one-path-spelling-in-guards.md` asks for.
- D3: **The guard is placed after `changed_all`, not at the mode choice at `:599`.** Context: `:599` is
  after the `if active_now:` block, so a guard there would run after the pointer checks have already
  emitted notes about a diff that does not exist. Decision: refuse at `:536`, before any of that.
  Consequence: the misleading pointer notes are never printed in this case.

## Gotchas found while reading the codebase
- G-1: `self_check` (`:571`) and its `rev` lambda (`:570`) live inside `if active_now:` (`:554-592`).
  With `.sdlc/active` empty they are never defined, so nothing outside that block may reference them.
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
  `sdlc-gate.yml:41` and `deploy.yml:49` (both `origin/<ref>` on clean CI checkouts). No caller passes a
  non-`HEAD` base on a tree that could be dirty.
- G-7: a `notes.append` guard would print its line and still end `CHAIN: PASS` (`:812-815`), reproducing
  the defect it was written to fix. Only `errors` or an early exit changes the verdict.

## Not doing
- The `gh`-absent crash in the same file. Separate defect, separate item.
- Making CI run the check against anything but a commit. CI is already correct here (G-2).
- Any change to how in-progress mode judges a diff that is genuinely non-empty.
- Fixing `work/run-queue/log.md:21`'s sha, found during this item's review. It belongs to another work
  item, and editing it here would take the pull request out of in-progress mode.
- Adding the eval-blank-line lesson to `knowledge/lessons/index.md`, which #55 left out. Same reason:
  it is not this item's file.
