---
type: lesson
title: Commit before the chain check, or it audits nothing and says so quietly
description: "check_artifact_chain.py diffs <base>...HEAD, so staged or uncommitted work is invisible to it; an empty diff is in-progress mode, and the check reports CHAIN: PASS against the pointer's item with a note claiming the diff touches only that item. Twice in one session it audited the wrong work."
tags: [lesson, chain-check, git, verify]
resource: ../../work/run-queue/
timestamp: 2026-09-08T19:35:00Z
---
# Commit before the chain check, or it audits nothing and says so quietly

## What happened
Twice in one session, on consecutive items. With a new intent written and staged but not committed,
`python3 scripts/check_artifact_chain.py --base origin/main` printed `CHAIN: PASS` under a note saying
the diff touched only `work/approve-by-dispatch/` — the *previous* item, still named by `.sdlc/active`.
Later, with the whole implementation of `work/run-queue` staged but not committed, the same command
printed the in-progress note for `work/run-queue/` and passed, having checked none of the code.

The mechanism: the check runs `git diff --name-only <base>...HEAD`, which sees only commits. Staged and
working-tree changes are not in `HEAD`, so the diff is empty, `all([])` is `True`, the check takes
in-progress mode, and the note it prints describes a diff that does not exist. `retire-active-pointer`'s
R-4 fixed the neighbouring case (a base ref git does not know) but not this one: here the ref is fine and
the diff is honestly empty.

## Rule
Commit, then check. `scripts/verify.sh` runs the chain check with `--base HEAD` and is unaffected; the
`--base origin/main` run that mirrors CI is only meaningful on a committed tree. The line to look for is
`note: mode: in-progress` on a change that plainly touches more than `work/<slug>/` — that note on a
code change means the check saw nothing.

## Where it is enforced
`scripts/check_artifact_chain.py`, since `work/run-queue-followups`. When the diff against `--base` is
empty, the caller did not pass `--base HEAD`, and `git status --porcelain` reports anything (or cannot be
read at all), the check refuses with one `  FAIL:` line naming how many paths it could not see and the
first three of them, then `CHAIN: FAIL`. `scripts/test_check_artifact_chain.py::DirtyTree` and
`evals/cases/chain-refuses-empty-diff-on-a-dirty-tree.yaml` hold it in place.

The rule above still stands for the one case the guard deliberately does not reach: `--base HEAD`, the
self-check `scripts/verify.sh` runs, whose diff is empty by construction and whose tree is *expected* to
be dirty, because the documented order of work is stage, verify, commit
([stage-new-files-before-verify.md](stage-new-files-before-verify.md)). A green `VERIFY: PASS` therefore
still says nothing about whether the commit you are about to make is complete.

The guard asks how the caller spelled `--base`, not which commit it resolves to. Those are not the same
question: in the scenario above the branch has no commits yet, so the base and `HEAD` *are* the same
commit, and the first design of this guard compared revisions and was therefore inert in the only case it
existed for. The record is `work/run-queue-followups/revisions/1.md`.
