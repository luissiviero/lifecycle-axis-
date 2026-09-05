---
type: sdlc/intent
id: agent-evals
title: Evals test the agent, and can go red
description: One prompt case among thirty-four, a nightly job that is green when the credential expires, fifteen hook cases whose negated assertions cannot fail, a path filter that misses half the config that steers the agent, and an approval-author check that reads prose.
stage: plan
status: approved
author: Luis Siviero (repo owner), drafted with Claude from the 2026-09-04 consensus list (item 8) and the Batch A follow-ups
approved-by: luissiviero
approved-on: 2026-09-05
supersedes:
record:
resource: https://claude.ai/code/session_01Te8oN2GdvRupSixH4kjR8Y
tags: [test, evals, ci, agent-evals, chain-check, consensus-item-8]
timestamp: 2026-09-05T03:10:00Z
---
# Intent: evals test the agent, and can go red

## Problem
The Test play says the kit keeps 20 to 50 evals drawn from real tasks, runs them on every change to the
configuration that steers the agent, and lets the pass rate gate config changes (`docs/sdlc/README.md:34`).
Six facts, each verified in the working tree (consensus item 8; Batch A follow-ups a and b):

1. `evals/cases/` holds thirty-four cases; one is a prompt case (`skill-intent-does-not-self-approve.yaml`).
   The other thirty-three are deterministic tests of hooks, checks and CI scripts that carry the eval label.
   Nothing exercises `/sdlc-spec`, `/sdlc-plan`, `/sdlc-incident`, the fix workflow, or the secrets hook as
   the agent meets it.
2. `scripts/run_evals.sh:68-74`: without `claude` and a credential, a prompt case is skipped and counted, and
   the run exits 0. The nightly `full-suite` job (`.github/workflows/agent-evals.yml:26-42`) is therefore
   green on the day the token expires, and stays green. Nothing about the agent's behaviour can ever go red.
3. Fifteen hook cases run under `set -e` and assert a refusal with a bare `! cmd` line that is not the last
   command of the check. Bash never triggers errexit on a negated command, so when the hook wrongly allows,
   the line's failure is ignored and the case passes. `hook-blocks-delete-and-glued-writes.yaml` has five
   such lines; `hook-blocks-verify-edit.yaml` three; the full list is in the spec. Those cases can only fail
   on their last line.
4. `agent-evals.yml:8` triggers on `CLAUDE.md`, `REVIEW.md`, `.claude/**`, `evals/**`, `.sdlc/**`,
   `scripts/**` and misses `docs/sdlc/rules/**` (the source `CLAUDE.md` is rendered from),
   `docs/sdlc/templates/**`, `GEMINI.md`, `AGENTS.md`, `.gemini/**` and `.claude-plugin/**`.
5. `scripts/check_artifact_chain.py:275` attributes an approval with `git log -S 'status: approved'`, which
   names the last commit that changed the *count* of that phrase anywhere in the file, prose included. On
   PR #25 an agent commit that mentioned the phrase in a deviation note was read as the approver and the
   chain check went red on a valid approval (`docs/sdlc/handoff/HANDOFF.md`, follow-up a).
6. The runner has no fixture step: a prompt case can only start from what the repository already holds, so a
   skill that needs an approved predecessor (`/sdlc-spec`, `/sdlc-plan`) cannot be evaluated. And the CI
   checkout is an untrusted workspace ("Ignoring 7 permissions.allow entries from .claude/settings.json:
   this workspace has not been trusted", every gate run's triage log), so a prompt case in CI may run with
   the project's hooks and permissions ignored.

## Proposed outcome
1. Five new `kind: skill` cases run the agent through the spec, plan, fix, secrets and incident behaviours
   and assert on the artifacts they leave, each in a temporary slug that the check removes.
2. `scripts/run_evals.sh --require-claude` counts a skipped prompt case as a failure; the nightly job uses it,
   so an expired credential is a red run. Local runs without a key keep skipping.
3. Every `! cmd` assertion in the fifteen cases fails the case when the command succeeds, and a verify check
   refuses a case that reintroduces the bare form.
4. The workflow's path filter covers every source that steers the agent, and the job can be started by hand.
5. The chain check attributes an approval to the commit whose diff added the `status: approved` line, not to
   a later commit that mentions the phrase; a regression test pins it.
6. A case may declare `setup:`, run before the prompt; the nightly job trusts the checkout so project hooks
   and permissions apply to `claude -p`.
7. `evals/README.md` and the README rows say which cases are gate tests and which are the playbook's evals,
   and that skill cases run nightly only. Tests cover the runner and the new check; `verify.sh`, the chain
   check, the evals and the OKF check are green.

## Affected users and systems
- Users: the owner (reads a red nightly run); an adopter who counts on the eval suite.
- Services / repos / data: `scripts/run_evals.sh`, `scripts/test_run_evals.py`, a new `scripts/check_eval_cases.py`
  with its `scripts/checks/eval-cases.sh` wrapper and test, `scripts/check_artifact_chain.py` and its test,
  `.github/workflows/agent-evals.yml`, twenty eval cases under `evals/cases/` (five new, fifteen fixed),
  `evals/README.md`, `docs/sdlc/README.md`.

## Constraints
- Must: keep prompt cases out of the PR-time job (never hand the credential to PR-head code; security review
  finding 4); keep `run_evals.sh`'s last line and exit contract; keep every existing case's intent (the fix
  makes the assertion effective, it does not change what is asserted); clean up every temporary slug and file
  a prompt case creates, whether the prompt succeeded or not; stay stdlib and bash.
- Must not: approve anything, commit anything, or open a PR from a prompt case; weaken a hook to make a case
  pass; touch `scripts/verify.sh`, `scripts/run_tests.py` or the hooks.
- Out of scope: the 20-to-50 target itself (five cases are the first real ones; adopters add their own);
  scoring rather than pass/fail (roadmap Phase 4); the `sdlc-gate` triage step's own trust problem (same
  fix, different item: `docs-reconcile`).

## Risk class
low — the runner, a check and a workflow change; every prompt case runs nightly on the default branch with the
existing credential scope; a wrong case costs one red nightly run, which is exactly the signal the item exists
to create. Product owner approves intent and spec; tech lead approves the plan (same person here).

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: Fold the two Batch A follow-ups into this item (the `! cmd` assertions, fact 3; the approval-author
  attribution, fact 5) rather than into `docs-reconcile`? The handoff left it to you.
  A: (proposed yes; both are tests that cannot go red, which is this item's subject)
- Q: Enforce the assertion rule with a new verify check under `scripts/checks/` (a control-plane path, so the
  PR needs your label) rather than a runner-time refusal?
  A: (proposed the check; it fails before the suite runs and names the file and line)
- Q: Keep skill cases nightly-only, with `workflow_dispatch` added so you can run the job by hand after merge?
  A: (proposed yes)
- Q: Attribute approvals with `git log -G '^status: approved$'` (a commit whose diff has that exact line)?
  A: (proposed yes)
