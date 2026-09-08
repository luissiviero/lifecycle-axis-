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
Nowhere yet. A guard in `check_artifact_chain.py` (refuse, or at least warn, when the diff is empty but
`git status --porcelain` is not) is a small `scripts/` change that needs a plan; until then this lesson
is the guard.
