---
type: sdlc/intent
id: advance-push
title: The post-merge advance never lands, because it pushes from a checkout older than the merge it follows
description: "delegated_merge.py advances .sdlc/active by committing on the job's checkout of main, taken before the merge API call moved main; the push is non-fast-forward every time and is swallowed as a note, so no queue has ever advanced live. Fetch and fast-forward onto the merged main before writing, with a regression test whose remote moves."
stage: plan
# status: draft | in-review | approved | delegated | superseded
status: in-review
author: Luis Siviero (repo owner); found and drafted by Claude while planning work/standing-grant and work/risk-detour, both of which depend on the queue advancing
# approved-by: product owner; set only by a human, with scripts/approve.py from their own shell
approved-by:
approved-on:
# risk-class: low | medium | high; the grant below is valid only for classes the policy lists
risk-class: low
# mode: supervised | delegated; delegated-by and delegated-on are set only by a human, like approved-by
mode: supervised
delegated-by:
delegated-on:
# supersedes: previous intent id, if any
supersedes:
# record: legacy system id (Jira/ServiceNow) if that system holds a copy
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/55
tags: [delegated-mode, run-queue, delegated-merge, active-pointer, fix]
timestamp: 2026-09-08T22:00:00Z
---
# Intent: the post-merge advance never lands, because it pushes from a checkout older than the merge it follows

## Problem
The owner, on 2026-09-08, describing where the project should go next: "I'd want no tap. I'd just start
writing and the mode was already delegated." Every design that gets there (`work/standing-grant`,
`work/risk-detour`) stands on one property `work/run-queue` promised: after a delegated pull request
merges, the merge workflow moves `.sdlc/active` to the next item and the run continues. Planning those
two items showed the property has never held.

Measured on 2026-09-08, on `main` at c0aa58c:

- `.github/workflows/delegated-merge.yml:77-79` makes the job's only checkout, of the default branch,
  before the script runs. That is by design (spec D6 of `work/delegated-mode`: never check out the head).
- `scripts/delegated_merge.py` merges through the API, which moves `main` to a new merge commit
  (`merge_method: merge`, never a fast-forward). The advance then commits on the job's checkout, whose
  `HEAD` is still the pre-merge `main`, and pushes `HEAD:main` (`delegated_merge.py:960-995`). There is
  no `fetch`, `pull` or `--ff-only` anywhere in the script (`grep -n "fetch\|ff-only" scripts/delegated_merge.py`
  returns nothing). The remote `main` is not an ancestor of the pushed commit, so the push is rejected
  as non-fast-forward, on every real merge, not only in a race.
- The rejection is swallowed on purpose: `delegated_merge.py:993-997` writes "advance commit not pushed
  (...); the next merge will advance" and returns. The comment above it reads the failure as "someone
  else pushed between the checkout and now". The someone else is the merge itself, so the next merge
  fails the same way.
- `git log --grep="Advance .sdlc/active"` on `main` is empty: no advance commit has ever landed. The
  suite is green because the fixture's bare remote never moves between the checkout and the push
  (`scripts/test_delegated_merge.py:1257-1271`), which is exactly the case production never produces.

So `work/run-queue`'s "zero human input between items" is, today, one merge and then an idle pointer
that still names the merged item. A second granted item is never opened.

## Proposed outcome
- After the merge API call succeeds, the advance runs on the merged `main`: it fetches the default
  branch and fast-forwards the checkout (or refuses, as a note, if that is not a fast-forward) before
  the dirty-tree check and before any write. Observable: the advance commit's parent is the merge commit
  the API returned, and the ledger note's "merged as <sha>" names that merge commit rather than the
  pre-merge `main`.
- A regression test whose bare remote receives a commit between the job's checkout and the advance, as
  the merge API does, asserts that the advance commit lands on the remote on top of that commit. The
  test fails on today's code (it is a `kind: fix` plan: the failing test comes first, then the code).
- The lost-update guard stays as it is: a push rejected after the fast-forward is still a note and
  never a retry (`work/run-queue` R-3, the non-forced push is the race guard). Observable: the existing
  rejected-push case in `test_delegated_merge.py` still passes unchanged.
- Nothing before the merge changes: every merge condition, the shallow checkout of `main`, the
  never-check-out-the-head rule, the staged-path allowlist and the `ALWAYS_LOCKED` floor are untouched.
  Observable: the existing `test_delegated_merge.py` cases pass unchanged; `scripts/verify.sh` ends
  `VERIFY: PASS`, the chain check `CHAIN: PASS`, the evals `0 fail`, `check_okf.py` `0 warnings`.

## Affected users and systems
- Users: the owner, whose granted queue currently stops after one merge; every `/sdlc-run` session.
- Services / repos / data: `scripts/delegated_merge.py` (a `locked-paths` entry in `.sdlc/delegation.yaml`,
  so this item's pull request is the owner's click); `scripts/test_delegated_merge.py`; one sentence in
  `knowledge/decisions/run-queue.md` recording that the advance shipped without a moving-remote test.

## Constraints
- Must: reproduce the defect as a failing test before the fix (plan `kind: fix`; the test files are
  locked once the plan is signed).
- Must: keep the advance additive and after the merge call, so a defect in it can never cause a wrong
  merge (`work/run-queue` plan, step 4).
- Must not: change the workflow file, the merge conditions, the checkout ref, or the allowlist of paths
  the advance may commit.
- Must not: retry a rejected push, force-push, or reset the checkout to anything but a fast-forward of
  the fetched default branch.
- Out of scope: the standing grant (`work/standing-grant`), the risk detour (`work/risk-detour`), the
  `.sdlc/active` line `work/run-queue/log.md:21` cites for another item (reported in pull request 56).

## Risk class
low — the change is confined to the write-back that runs after a successful merge, and the merge
itself is untouched. Getting the fix wrong reproduces today's behaviour (no advance, a note in the job
summary), which is visible in the ledger and recoverable with a tap. The item's pull request merges by
the owner's click regardless, because `scripts/delegated_merge.py` is a locked path.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: fetch-and-fast-forward, or re-checkout? Proposed: `git fetch origin <default>` then
  `git merge --ff-only FETCH_HEAD` on the job's checkout; a non-fast-forward result is a note and no
  write, the same shape as the rejected push today.
  A: agreed (owner, 2026-09-08): fetch the default branch, then `git merge --ff-only FETCH_HEAD`; a non-fast-forward result is a note and no write.
- Q: should the advance also check that the fetched tip is the merge commit the API returned before
  writing? Proposed: yes; it is one comparison, it makes the ledger's "merged as <sha>" exact, and a
  mismatch (someone pushed to `main` in the same second) is a note and no write.
  A: agreed (owner, 2026-09-08): compare the fetched tip with the merge commit the API returned before writing; a mismatch is a note and no write.
- Q: this item must merge before `work/standing-grant` or `work/risk-detour` can be demonstrated live.
  Grant it first, or run it supervised? Proposed: supervised; it is one locked file and one test.
  A: agreed (owner, 2026-09-08): supervised, and first of the three items.
