---
type: sdlc/intent
id: deploy-gate
title: The deploy path fails open; every route to production must fail closed on a named human
description: RELEASE_APPROVAL is derived from the commit it is meant to approve, the gate hook misses the gh and deploy.sh routes, deploy.sh is satisfied by three exported variables, and a release authorization file is never checked against the approvers list.
stage: plan
status: approved
author: Luis Siviero (repo owner), drafted with Claude from the 2026-09-04 consensus list (item 4)
approved-by: luissiviero
approved-on: 2026-09-05
supersedes:
record:
resource: https://claude.ai/code/session_01DSYmeD7eng2GKQ3EbHQDzo
tags: [deploy, production-gate, release-authorization, hooks, ci, consensus-item-4]
timestamp: 2026-09-04T21:50:29Z
---
# Intent: the deploy path fails open; every route to production must fail closed on a named human

## Problem
Rule 4 says "a human authorizes releases" and `knowledge/decisions/deploy-from-ci.md` says the deploy
path fails closed. The code says otherwise; five facts, each verified in the working tree (consensus item 4):

1. `.github/workflows/deploy.yml:55` sets `RELEASE_APPROVAL: ${{ inputs.sha || github.sha }}` and `:42`
   checks out that same ref, so inside CI the approval always equals HEAD and the comparison at
   `scripts/deploy.sh:83` holds by construction. No human produced the value, and on this repo the
   Environment reviewers the workflow header (`:7-8`) relies on are not enforceable
   (`merge-click-is-the-gate.md:43-45`).
2. `.claude/hooks/production-gate.sh:26` names specific tools. `gh release create` (fires `deploy.yml:23-24`
   `release: published`), `gh workflow run deploy.yml` (fires `workflow_dispatch`) and `gh pr merge` (the
   release act here, `merge-click-is-the-gate.md:32-33`) match nothing at `:90`, so an unattended session
   runs them with no prompt. `push_reaches_protected()` reads only `git push`.
3. `scripts/deploy.sh:70-73` "CI only" tests `[ -z "${CI:-}" ]`; `:91` tests `GITHUB_ACTIONS`. Exporting
   `CI=1 GITHUB_ACTIONS=true RELEASE_APPROVAL=$(git rev-parse HEAD)` on any machine prints
   `DEPLOY: would run ... for production`, and `scripts/test_deploy_guard.py:113-121`
   (`test_production_with_github_actions_succeeds`) asserts exactly that as success, while
   `deploy-from-ci.md:40-43` says it "cannot be satisfied by exporting the two env vars locally".
4. The playbook's generic match, `deploy` and `prod|production` in one command, was not carried into the
   hook (no revision since `0d00f91` has it), so `make deploy ENV=production`, `./scripts/deploy.sh production`
   and `./deploy production` are not gated.
5. `production-gate.sh:93` accepts `.sdlc/release-authorizations/<sha>` on `grep -q '^approved-by:'` alone;
   the handle is never checked against `.sdlc/approvers.yaml` (`release-manager` at `:12`, `never-approve`
   at `:26`), so `approved-by: claude` passes. `scripts/deploy.sh` never reads the file. Under this repo's
   control-plane unlock (`protect-paths.sh:24-25`, `knowledge/decisions/self-hooks-on.md`) an agent can write it.

Who is affected: the owner, whose release guarantee is a comment; adopters who copy `deploy.yml` and
`deploy.sh` trusting the decision record; every unattended or Gemini session the gate is meant to block. How
we know: this session's adversarial run drove each route through `scripts/hooktest.py` and a scratch clone.

## Proposed outcome
- `production-gate.sh` honours a release authorization file only when `approved-by` holds `release-manager`
  in `.sdlc/approvers.yaml` (never-approve rejected); any other file is ignored and the command asks, or
  blocks when unattended. Allow and reject are logged.
- `gh release create`, `gh workflow run`, `gh pr merge`, `deploy.sh` in command position, `deploy` with
  `prod|production`, and a mutating `gh api` on `releases|merges|dispatches` ask (block unattended);
  `deploy --help`, `gh pr view 12`, `gh api repos/o/r/releases/latest`, `git log --grep=deploy` stay allowed.
- `deploy.yml` reads `RELEASE_APPROVAL` from an Environment secret a human stores; an unapproved run
  refuses naming both SHAs.
- `scripts/deploy.sh` accepts a committed `.sdlc/release-authorizations/<sha>` only when
  `python3 scripts/approvers.py --has-role release-manager <handle>` exits 0; `CI`/`GITHUB_ACTIONS` stay as hints.
- Decision records, runbook, `environments.yaml` and README rows say what the code does.
- Tests grow by the authorization, deploy-shape and file-route cases; `scripts/verify.sh` green; evals `0 fail`.

## Affected users and systems
- Users: the owner (release manager); adopters of `deploy.yml`/`deploy.sh`; Claude Code and Gemini sessions
  running `gh` or deploy-shaped commands.
- Services / repos / data: this repo only. `production-gate.sh`, `deploy.yml`, `scripts/deploy.sh`, their tests
  and evals, `.sdlc/environments.yaml`, `.sdlc/README.md`, `docs/sdlc/README.md`, two decision records, the runbook.

## Constraints
- Must: keep the hook a nudge (`ask`, or `block` when unattended or under Gemini); never emit
  `permissionDecision: allow`; every verdict that passes today stays, except the routes above.
- Must: bash+awk only in the hook; `deploy.sh` may call `python3 scripts/approvers.py` (Linux CI only).
- Must: keep the `DEPLOY: would run` and `deploy refused:` shapes and the `VERIFY:`/`CHAIN:`/`EVALS:` lines.
- Must not: write `.sdlc/release-authorizations/<sha>` or set `RELEASE_APPROVAL` from an agent session,
  this item's PR included; fixtures live in temp repos only.
- Out of scope: deploy/rollback as MCP tools, a real deploy command, a GitHub plan change, the never-unlock
  `case` in `protect-paths.sh` (`control-plane-visibility` item), the approval hook (`approval-gate` item).

## Risk class
low — `deploy.sh` executes nothing (it echoes), the hook only prompts or blocks, and the workflow change makes
CI refuse rather than deploy. Blast radius: this repo's tooling and adopters. No data; the secret is named, not held.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: `gh pr merge` will prompt on every merge; `merge-click-is-the-gate.md:32-33` has the owner instructing
  the agent to merge in chat. Is the prompt acceptable as that click? Proposed: yes; the record says so.
  A:
- Q: Keep the Environment-secret route beside the file route? Proposed: yes; adopters with real reviewers need it.
  A:
- Q: Runbook passes the 40-hex SHA, not a tag (`deploy.sh:83` compares SHAs; `deploy.yml` has no `ref` input)? Proposed: yes.
  A:
