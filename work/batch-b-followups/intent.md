---
type: sdlc/intent
id: batch-b-followups
title: Close the three leftovers Batch B surfaced
description: "The sdlc-gate triage step runs untrusted, the adopter placeholder handle can approve, and the chain check rejects a fully retired item; three small fixes the last work items named but could not make."
stage: plan
status: in-review
author: Luis Siviero (repo owner), drafted with Claude from the follow-ups recorded on pull requests 37 and 38
approved-by:
approved-on:
supersedes:
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/37
tags: [followups, sdlc-gate, adopt, chain-check, control-plane]
timestamp: 2026-09-05T05:25:00Z
---
# Intent: close the three leftovers Batch B surfaced

## Problem
Three defects were found while finishing the 2026-09-04 plan, each recorded where it was found and each
too small or too far outside its finder's approved plan to fix there. They have three different origins, so
the front matter's single `resource:` link cannot carry them all: defect 1 was recorded on pull request 37,
defect 2 in `work/adopter-first-hour` spec C1 and again on pull request 37, defect 3 on pull request 38.

1. **The `sdlc-gate` triage step runs Claude untrusted.** Every failing run logs "Ignoring 7
   permissions.allow entries from .claude/settings.json: this workspace has not been trusted", so the
   read-only triage runs without the repository's own permission settings. `agent-evals.yml` already
   solves this with a trust step (`work/agent-evals`); `sdlc-gate.yml` never got it. Found on every red
   `sdlc-gate` run of Batch B; recorded on PR #37.
2. **The adopter placeholder handle can approve.** `adopt.sh` writes `<your-github-handle>` into every
   role of the copied `.sdlc/approvers.yaml`. Until the adopter replaces it, `scripts/approve.py --as
   '<your-github-handle>'` approves `work/_example` and the plan gate opens on a name that is nobody.
   `work/adopter-first-hour` spec C1 noted a `never-approve` entry as "the same thing said louder" and
   deferred it to `docs-reconcile`, which withdrew it because `scripts/test_adopt.py` asserts the current
   behaviour and `docs/sdlc/github-setup.md` documents it. It is a change to a test, two documents and a
   human-only file together, so it needs its own item.
3. **The chain check rejects a fully retired item.** `check_artifact_chain.py`'s in-progress mode applies
   "one stage at a time": an artifact may exist only if its predecessor is `approved`. After Step 0 of the
   plan (the owner set `work/sdlc-kit-phase-1`'s three artifacts to `superseded`, which the same script's
   supersession branch validates correctly), the rule reports `spec.md exists but intent.md is
   'superseded', not 'approved'`, so PR #38 (the index regeneration Step 0 required) is red on a check
   that should pass. The plan's author expected supersession to validate (PLAN.md Step 0).

A fourth, smaller item rides along: `docs/sdlc/handoff/HANDOFF.md` still says Batch B is pending and
Step 0 is not done.

Who is affected: whoever reads a triage summary (1); every adopter in their first hour (2); any PR that
touches a retired work item, starting with #38 (3). How we know: the CI logs of every red `sdlc-gate` run;
`scripts/test_adopt.py::test_handle_rewritten` (asserts the placeholder holds `tech-lead`); the chain
check output on PR #38.

## Proposed outcome
- A failing `sdlc-gate` run's triage step no longer logs the "workspace has not been trusted" line; the
  step is the one `agent-evals.yml` uses, nothing more.
- On a fresh `adopt.sh` target, `python3 scripts/approvers.py --has-role tech-lead '<your-github-handle>'`
  exits 1 and `approve.py --as '<your-github-handle>'` is refused until the handle is replaced;
  `github-setup.md` step 1 and `adopt-script.md` say so; the adopter test asserts it.
- `python3 scripts/check_artifact_chain.py --base 2190c0c --slug sdlc-kit-phase-1` ends `CHAIN: PASS` on
  `main`: a `superseded` predecessor satisfies the stage-order rule; a regression test pins it; the three
  existing supersession tests still pass.
- `HANDOFF.md` states the task state as of this item: Batch B merged, Step 0 done, this item open.

## Affected users and systems
- Users: the owner; adopters; every PR that touches a retired item.
- Services / repos / data: `.github/workflows/sdlc-gate.yml` (control plane: label), `.sdlc/approvers.yaml`
  (human-only file: the owner edits it from the web editor, the session may not), `scripts/check_artifact_chain.py`
  and its tests, `scripts/test_adopt.py`, `docs/sdlc/github-setup.md`, `knowledge/decisions/adopt-script.md`,
  `docs/sdlc/handoff/HANDOFF.md`, `.sdlc/active`.

## Constraints
- Must: keep the triage step read-only and step-scoped for the credential, as it is now; the trust step
  writes only `~/.claude.json` on the runner.
- Must: change the adopter test to assert the new behaviour, not delete it; keep the placeholder visible
  in every file it is in today.
- Must: keep every existing chain-check test green; the fix widens one comparison, nothing else.
- Must not: touch `.claude/hooks/`, `.claude/settings.json`, `scripts/verify.sh`, the two runners,
  `scripts/checks/`; `.sdlc/approvers.yaml` is edited by the owner only (the hooks refuse the session, with
  or without the unlock).
- Out of scope: the other B13 faults; the review workflow's base-branch restore (by design); Phase 2.

## Risk class
low — one workflow step copied from a sibling workflow, one list entry in a YAML file, one comparison in
a Python check, two documents and two tests. Blast radius: CI triage output, the adopter's first hour, and
which PRs the chain check accepts. Reversal is a revert.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: The `never-approve` entry blocks the placeholder everywhere `approvers.py` is consulted, including the
  hooks (`require-plan.sh` reads the plan's `approved-by` through `approver_has_role`). On a fresh target
  that means the plan gate stays closed until the handle is replaced, which is the intended effect. Accept
  that an adopter who skips step 1 gets a blocked `Edit` under `PLAN_REQUIRED_PATHS` with the hook's
  message naming `approvers.yaml`?
  A: (proposed by the session on 2026-09-05; edit before approving) Yes. That is the first-hour order
  `github-setup.md` already prescribes (replace the handle, then approve); the block names the file to fix.
- Q: Three unrelated fixes in one item, or three items? Each is under twenty lines; three items would cost
  nine approvals and three labels.
  A: (proposed) One item. The spec keeps them as separate requirements with separate oracles, so the PR
  reads as three fixes; a reviewer can still object to one without the others.
