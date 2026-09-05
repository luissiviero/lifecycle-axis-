---
type: sdlc/intent
id: approval-gate
title: Only a human can flip an artifact to approved
description: No hook covers work/, so an agent can set status approved and approved-by itself or run approve.py with CLAUDECODE stripped, and the chain check does not catch a local agent; approval is a record, not a gate.
stage: plan
status: approved
author: Luis Siviero (repo owner), drafted with Claude from the 2026-09-04 playbook comparison
approved-by: luissiviero
approved-on: 2026-09-05
supersedes:
record:
resource: https://claude.ai/code/session_01DSYmeD7eng2GKQ3EbHQDzo
tags: [hooks, approvals, chain-check, approve, consensus-item-1]
timestamp: 2026-09-04T21:49:27Z
---
# Intent: only a human can flip an artifact to approved

## Problem
The approval stack (`scripts/approve.py`, `.sdlc/approvers.yaml`, the `log.md` ledger, the chain check)
is the kit's most important control and today it is a record, not a lock. Verified in the working tree:

- No hook covers `work/`. `.sdlc/config.env:7` protects `.claude/hooks .github/workflows .sdlc .gemini`
  and `:4` plan-gates `scripts` only, so an agent can Edit `work/<slug>/plan.md` to `status: approved`
  with `approved-by: luissiviero` and no hook says a word.
- `scripts/approve.py` refuses under `CLAUDECODE` (`:70-73`), but `env -u CLAUDECODE python3
  scripts/approve.py <slug> plan.md --as luissiviero` runs it from a Bash tool call. Its own docstring
  says so (`approve.py:21`): "That refusal is a courtesy, not a gate (an environment variable can be
  stripped)".
- The backstop it points at does not hold locally. `scripts/check_artifact_chain.py:84` recognises an
  agent author only by email shape (`@anthropic.com`, `[bot]@`, `noreply@`) or a never-approve handle
  (`:87-94`), and the commit-author check at `:241-265` reads whatever identity `git config` holds. A
  local agent commits as the owner, so `CHAIN: PASS` follows a forged approval.
- `require-plan.sh:19-20` compares the `status:` string to `approved` and never reads `approved-by`,
  so a plan "approved" by nobody, or by `claude`, opens every plan-required path.

The reconciliation of the two analyses (`scratchpad/consensus.md`, row 3) gave the verdict "keep the
design; it is not yet a gate", and its merged fix list puts this first: consensus item 1, "make the
approval stack a gate (hook on `work/*` status fields; Bash rule for `approve.py`; validate
`approved-by` in the release gate)". Affected: the owner, whose approval is the only human gate here,
and every adopter. How we know: the adversarial run reproduced each route (`scratchpad/bypass_table.md`).

## Proposed outcome
- A new hook, `.claude/hooks/protect-approvals.sh`, blocks (exit 2) any Edit, Write, MultiEdit or
  NotebookEdit to `work/<slug>/{intent,spec,plan,incident}.md` whose new text sets `status:` to
  `approved` or `superseded`, or a non-empty `approved-by:`/`approved-on:` that differs from the
  file's current value. Editing an approved plan's deviations log still passes.
- The same hook blocks Bash commands that invoke `approve.py`, that unset or reassign `CLAUDECODE`,
  or that write a chain artifact while mentioning approval. `SDLC_CONTROL_PLANE_UNLOCK` never applies.
- `require-plan.sh` also requires `approved-by` to hold the plan's role in `.sdlc/approvers.yaml`
  (`tech-lead` today) and not be in `never-approve`; a missing approvers file fails closed.
- The hook is wired in `.claude/settings.json`, the adopter template and `.gemini/settings.json`.
- Tests: new `scripts/test_protect_approvals.py` (eight block cases, six allow cases) and four new
  `RequirePlanHook` cases; eval `hook-blocks-agent-approval.yaml`; `scripts/verify.sh` stays green.
- After this lands: in a fresh session an Edit flipping `work/x/intent.md` to `status: approved` is
  blocked, `python3 scripts/approve.py ...` from Bash is blocked, and the owner's shell approval works.

## Affected users and systems
- Users: the owner (approvals from their own shell are unchanged); every Claude Code and Gemini
  session in this repo and in adopters that install hooks.
- Services / repos / data: this repo only. `.claude/hooks/protect-approvals.sh` (new), `require-plan.sh`,
  the three settings files, the hook tests, one new eval, one new decision record, the rule fragments.

## Constraints
- Must: keep bash+awk+jq in hooks (no `python3` call: it imports `check_artifact_chain`, which runs
  `git rev-parse` at import, and may be the Store stub on Windows); reuse `fm_value`,
  `artifact_role` and `approver_has_role` from `_lib.sh` (landed by `control-plane-visibility`).
- Must: leave every existing hook verdict unchanged except `require-plan.sh` on a plan whose
  `approved-by` is empty, invalid or a never-approve identity, which now blocks.
- Must not: block drafting. `status: in-review`, a verbatim template copy, and edits to an approved
  artifact that repeat its current approval values all pass.
- Must not: honour the unlock; this hook has no bypass in any environment.
- Out of scope: the release-authorization approver check (`deploy-gate`), the CI trailer detection
  (`control-plane-visibility`), the adopter copy list (`adopter-first-hour`).

## Risk class
low, with one operational caveat: this is the last hook item and the most restrictive one. A defect
would lock the session out of drafting artifacts, and the wiring is read at session start, so the
session restarts after it lands. No data, no secrets, no deploy path; blast radius is this repo's
tooling and any adopter that copies it.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: Should a demotion (an agent editing `status: approved` back to `in-review`) also be blocked?
  Proposed: no; it only loses an approval, the chain check flags it, and blocking it would stop the
  owner-instructed supersede flow from being drafted. Re-approval is what the hook refuses.
  A:
- Q: Should the Bash rule that blocks any command mentioning `approved|supersed` while writing a
  chain artifact be narrowed to the front-matter keys? Proposed: keep it broad; a false positive
  costs one retry with the Write tool, a false negative costs the gate.
  A:
