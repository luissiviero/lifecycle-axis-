---
type: sdlc/intent
id: approve-tap-regenerates-index
title: The approval tap commits an approval whose indexes are stale; make the tap regenerate what it changes
description: "The approve workflow runs the approval script and commits, but nothing in it runs gen_index.py, so every tap so far has left work/<slug>/index.md and work/index.md drifted on the ref it wrote to, and the committer's allowlist documents a regeneration that does not happen. This item makes the tap regenerate both indexes and commit them, and nothing else."
stage: plan
status: in-review
author: Luis Siviero (repo owner), who reported the defect with the evidence below; drafted by Claude from the three tap commits on main and the committer's own allowlist
approved-by:
approved-on:
risk-class: low
mode: supervised
delegated-by:
delegated-on:
supersedes:
record:
resource: https://github.com/luissiviero/lifecycle-axis-/commit/c0aa58c
tags: [approvals, workflow-dispatch, gen-index, index-drift, control-plane, verify]
timestamp: 2026-09-08T21:50:00Z
---
# Intent: the approval tap commits an approval whose indexes are stale

## Problem
In the owner's words: "the approval tap (`.github/workflows/approve.yml`, which runs `scripts/approve.py`
then `scripts/approve_dispatch.py --commit`) does not regenerate indexes."

The evidence, measured on 2026-09-08 against `main`:

- Commit c0aa58c, "[run-queue-followups] Approve intent.md as luissiviero", is the tap's own commit. It
  touched three files: `.sdlc/active`, `work/run-queue-followups/intent.md` and
  `work/run-queue-followups/log.md`.
- On that commit `python3 scripts/gen_index.py --check` prints `work/run-queue-followups/index.md: drifted`,
  `work/index.md: drifted`, `INDEX: 2 file(s) drifted` and exits 1. `scripts/checks/index-drift.sh` runs
  that command for `scripts/verify.sh`, so verify is red on a clean checkout of main.
- Every tap so far has the same shape. 3da8bb6 (`run-queue`) and a903a91 (`retire-active-pointer`) each
  committed exactly those three paths and no `index.md`.
- `scripts/approve_dispatch.py` names `index.md` in `CHAIN_FILES`, and the comment above it says
  "gen_index.py's index.md is regenerated in the same tree". Nothing in `.github/workflows/approve.yml`
  runs `gen_index.py`, so the sentence describes a step that does not exist. `work/index.md`, the second
  file the generator writes, is not in the allowlist at all: had the generator run, `unexpected_paths`
  would have named it as a stray path and the committer would have refused the commit.

Why three taps went by unnoticed: `sdlc-gate.yml` runs on pull requests only, never on a push to main, and
the next commit on each item was an agent's, which regenerates before committing as `CLAUDE.md` says to
(5ff9f5d, the `run-queue` spec, carried the two indexes 3da8bb6 had left stale). The drift is real in the
window between the tap and that commit: a branch cut from main inside it fails verify on a file nobody
edited, and anyone running `scripts/verify.sh` on main sees `VERIFY: FAIL`. Today that window is open:
`run-queue-followups` was approved by c0aa58c and no later commit has regenerated its index.

## Proposed outcome
- A tap commits the approval and the two regenerated indexes, and nothing else. Observable: the next tap
  commit on main touches `work/<slug>/index.md` and `work/index.md` beside the artifact, `log.md` and, for
  a grant, `.sdlc/active`; `python3 scripts/gen_index.py --check` on that commit prints `INDEX: up to date`.
- The committer's allowlist says what is true: it names both generated files, and its comment names the
  step that regenerates them. Observable: `scripts/test_approve_dispatch.py` gains a case that writes an
  approval, regenerates the indexes with `scripts/gen_index.py` the way the workflow will, commits, and
  asserts the committed set is exactly the artifact, `log.md`, `work/<slug>/index.md` and `work/index.md`.
  The case fails on today's code, where `work/index.md` is a stray path.
- The stray-path guard keeps its strength: a path outside the allowlist still aborts the commit and is
  named in the refusal. Observable: the existing cases in `scripts/test_approve_dispatch.py` pass
  unmodified.
- Everything ends green: `scripts/verify.sh` `VERIFY: PASS`, `check_artifact_chain.py` `CHAIN: PASS`,
  `scripts/run_evals.sh` `0 fail`, `scripts/check_okf.py` `0 warnings`.

## Affected users and systems
- Users: the owner, whose every tap today leaves main red on verify until the next agent commit; every
  session and every human who runs `scripts/verify.sh` on a checkout cut from main in that window.
- Services / repos / data: `.github/workflows/approve.yml` (one step between Approve and Commit and push);
  `scripts/approve_dispatch.py` (the allowlist and its comment); `scripts/test_approve_dispatch.py` (the
  regression case). The workflow is in `PROTECTED_PATHS`, so the pull request needs the owner's
  `control-plane-approved` label and the owner's merge click; `scripts/` is in `PLAN_REQUIRED_PATHS`, so
  the edits need an approved or signed plan first.

## Constraints
- Must: regenerate with `scripts/gen_index.py` itself, never a second renderer, so the tap's index is
  byte-identical to what a session or `scripts/checks/index-drift.sh` would produce.
- Must: keep the workflow's stated properties: one checkout of the dispatch ref, no pull-request head code
  executed, no dependency installed (`gen_index.py` and the two modules it imports are stdlib only), and a
  committer that refuses any path outside the item's chain files, the two indexes and `.sdlc/active`.
- Must: leave `scripts/approve.py` untouched. It is on the policy's `locked-paths`, and decision 3 of
  `knowledge/decisions/approve-by-dispatch.md` keeps the tap's run of it byte-identical to a plain run;
  the regeneration goes around the script, not inside it.
- Must: carry a regression test that fails without the change, in the file that already tests the committer.
- Must not: widen the allowlist beyond the two generated files; touch `.sdlc/`, `.claude/hooks/`,
  `scripts/verify.sh`, `scripts/checks/` or any other workflow; change what the tap writes to the artifact
  or the ledger.
- Out of scope: the drift already on main from c0aa58c (this item's own pull request cannot carry
  `work/run-queue-followups/index.md` without leaving in-progress mode, so it is left to that item's next
  commit or to the owner, and reported); running `sdlc-gate` on pushes to main; guarding a human's
  hand-made approval commit against the same omission.

## Risk class
low — one workflow step that runs a generator every session already runs, one allowlist entry, one test.
If the step fails, the run fails before Commit and push, and the runner's tree is discarded: nothing is
pushed. If the generator writes something unexpected, the committer refuses the stray path as it does
today. Blast radius: the tap's commit gains two generated files; reversal is deleting the step and the
entry. The permissions block does not change, so `scripts/checks/workflow-permissions.sh` sees the same
workflow. The same value is in the `risk-class` key above, and the policy delegates `low`.

One thing the owner should weigh before choosing the mode, because it decides where this item goes:
`.github/workflows/approve.yml` is in `PROTECTED_PATHS`, so the merge script refuses this item's pull
request and the `sdlc-run` skill ends the queue at it. Under a grant the agent signs spec and plan and
opens the pull request; the label and the merge click are the owner's either way, so grant it last, or run
it supervised.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: regenerate in the workflow, as a step between Approve and Commit and push, or inside
  `scripts/approve_dispatch.py --commit`, which would import `gen_index` and write the two files before
  staging? Proposed: the workflow step, as reported. It mirrors what a human does after the approval
  script in their own shell (approve, regenerate, commit), keeps `--commit` a pure committer that stages
  what it finds and refuses what it should not, and puts the command in the run log. The cost is one line
  in a protected file, which is what makes the pull request the owner's click; the in-script route would
  avoid the protected path at the price of a committer that also writes.
  A:
- Q: when regeneration changes an index the tap may not commit (another item's, drifted on main before the
  tap, exactly main's state today), should the tap refuse, or stage only its two files and push a tree it
  knows is stale elsewhere? Proposed: refuse, which is what the existing guard already does, with the path
  in the message so the owner learns main was already drifted and the fix is one regenerate-and-commit.
  Staging around it would mean widening a guard's input, and that guard was tuned by its own tests.
  A:
