---
type: lesson
title: A test that reads the ambient environment passes here and fails on the runner
description: "Two tests in one pull request passed locally and failed or flaked in CI, both because they inherited something the session had and a runner does not: a global git identity, and a wall-clock second that happened not to tick. A fixture supplies every input it depends on, including identity and time."
tags: [lesson, tests, ci, fixtures, git]
resource: ../../scripts/test_check_artifact_chain.py
timestamp: 2026-09-06T19:40:00Z
---
# A test that reads the ambient environment passes here and fails on the runner

## What happened
Twice in `work/approve-by-dispatch`, in the same pull request.

1. `test_trailers_are_read_from_the_commit_body` called a bare `git commit` instead of the file's own
   `_commit()` helper. This session's container has a global git identity, so it passed; the CI
   runner has none, so `git commit` exited 128 and took `VERIFY` down with it. The helper that sets
   `-c user.email` / `-c user.name` was three lines above, already used by every other test in the
   file.
2. `test_writes_the_same_files_as_a_plain_run` compared two generated `log.md` files after
   normalising the ledger line's timestamp — but not the front-matter `timestamp:` the header
   carries. Two fixtures created a second apart differ there. It passed in isolation, where the two
   runs land inside one second, and went red only in a full-suite run. The plan-conformance review
   found it; a slower CI box would have found it later and less politely.

Both are the same mistake: the test depended on something the environment happened to supply
(an identity, a clock that did not tick) rather than on something the fixture set.

## Rule
A fixture supplies every input the test depends on — identity, time, paths, environment variables —
or normalises it before comparing. Never let a test read the developer's machine. Two cheap checks
before pushing a new test:

- `HOME=/tmp/empty GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null python3 scripts/run_tests.py`
  reproduces a runner with no git identity.
- Run the whole suite, not just the new test: a comparison that straddles a wall-clock boundary only
  fails when something slow runs before it.

## Where it is enforced
Prose and review. `scripts/run_tests.py` runs every suite, so a full-suite run is the check that
catches the timing class; the git-identity class has no automated guard beyond CI itself.
