---
type: lesson
title: A tap or a web-editor retirement commits no index; check main for drift before you cut a branch
description: "approve.yml and a web-editor retirement each commit the artifact, the ledger and the pointer and never run gen_index.py, so main is VERIFY: FAIL on work/index.md and work/<slug>/index.md until someone regenerates them. Seen three times in one day, each time paid for by a pull request on files nobody edited; the regeneration must ride under the item whose index it is, because the chain check reads one work item at a time."
tags: [lesson, gen-index, approvals, retirement, verify, chain-check]
resource: ../../work/approve-tap-regenerates-index/
timestamp: 2026-09-14T02:30:00Z
---
# A tap or a web-editor retirement commits no index; check `main` for drift before you cut a branch

## What happened
Three times on 2026-09-14, each on `main` and each on files no pull request had touched:

- `a9a40d5` — the owner retired `session-chaining` from the web editor: three artifacts to `superseded`,
  three ledger lines, no index. `gen_index.py --check`: `2 file(s) drifted`. Cleaned by #78.
- `b30feff` and `70437ab` — the owner approved `advance-push` and `approve-tap-regenerates-index` with the
  tap: each commit carried `intent.md`, `log.md`, `.sdlc/active` and no index. `3 file(s) drifted`,
  `VERIFY: FAIL`. Cleaned by #80 and #81 — **two** pull requests, because a single one carrying both items'
  indexes is in-progress mode for neither slug and the chain check demands a full approved chain neither
  item had yet.

The second incident was the tap approving the very item whose intent describes the defect.

The mechanism is the same on both routes: `.github/workflows/approve.yml` runs the approval script and
`scripts/approve_dispatch.py --commit`, and nothing in that path runs `gen_index.py`; the web editor runs
nothing at all. `sdlc-gate` runs on pull requests only, never on a push to `main`, so the drift is invisible
until the next branch is cut — and then it is that branch's red gate.

## Rule
After any human-side commit that changes an artifact's front matter — a tap, a grant, a retirement, a
web-editor edit — and before cutting a branch from `main`:

```
git fetch origin main && python3 scripts/gen_index.py --check
```

If it prints `drifted`, regenerate and carry the fix in the first pull request, under the item whose index
it is: `Work-Item: <that slug>`, one item per pull request, so the chain check takes in-progress mode. A
clean-up that must span two items is two pull requests. Never fold another item's index into a code pull
request "while you are there": it drops that pull request out of in-progress mode.

A red `index-drift` on a branch that did not touch the file is this defect, not the branch's: say so once,
regenerate, and move on. Do not treat it as a flake.

## Where it is enforced
On the tap route, for approvals and retirements alike: `work/approve-tap-regenerates-index` put the
regeneration inside `approve_dispatch.py --commit` with the allowlist widened to the generated indexes, and
`work/retire-delegated-items` made a retirement the same tap (`mode: retire`), so its commit goes through the
same committer. The web-editor route, for either act, still commits no index; until a hook or a check makes
that route impossible, this pointer stays and the first command after a web-editor commit on `main` is
`python3 scripts/gen_index.py --check`.
