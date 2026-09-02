---
type: decision
title: CI is informational; the merge click is the gate
description: This private repository sits on the GitHub Free plan, where branch protection, rulesets and environment protection rules are unavailable (HTTP 403). The owner chose to keep it that way: every check still runs and reports on each PR, the control-plane job still blocks bot-authored control-plane diffs until a human labels them, and the merge itself is the human gate, clicked by the owner or performed by the agent on the owner's explicit instruction.
tags: [github, branch-protection, governance, sdlc]
timestamp: 2026-09-02T22:50:00Z
---

# CI is informational; the merge click is the gate

## Context

The playbook, `deploy.yml`, `.sdlc/environments.yaml` and the spike checklist in
`docs/sdlc/spikes/pr-review-identity.md` assume protected branches: required status checks,
required reviews, no force pushes, and GitHub Environments with required reviewers for
production. On 2026-09-02 every one of those endpoints answered
`403 Upgrade to GitHub Pro or make this repository public` for this repo. That is a plan
limit, not a misconfiguration: private repositories on the Free plan get none of them; public
repositories and paid plans get all of them.

## Decision

The owner chose, on 2026-09-02, to keep the repo private on the Free plan and accept that
**CI is informational and the merge click is the gate**:

- Every workflow keeps running on every PR and reports its result on the merge button:
  `sdlc-gate` (chain, verify, control plane), `agent-evals`, `pr-review`.
- `scripts/check_control_plane.sh` keeps failing the gate for a bot-authored or `claude/*`
  diff under `PROTECTED_PATHS` until a human applies `control-plane-approved`. Dependabot's
  workflow bumps go through exactly that route (first case: PR #5).
- The human act is the merge. The owner reads the checks and clicks, or tells the agent in
  chat to merge specific PRs, which the agent then does with the owner's `gh` login. A merge
  the owner did not ask for is out of bounds regardless of how green the checks are.
- Nothing pushes to `main` directly. `production-gate.sh` turns a direct push into a
  permission prompt and refuses force pushes and hard resets outright.

## Consequences

- A red check does not stop a merge; the person clicking has to look. `gh pr checks <n>`
  before merging is the habit that replaces the protection rule.
- CODEOWNERS routing works, the *requirement* for a code-owner review does not. Reviews are
  advisory, as the kit already treats them.
- `deploy.yml`'s environment approval is not enforceable here; `scripts/deploy.sh` still
  refuses without `RELEASE_APPROVAL` bound to the exact commit, so the deploy path fails
  closed rather than open.
- Adopters on a paid plan or a public repo should still apply the spike checklist; the
  `adopt.sh` next-steps say so.
- Revisit if the repo goes public or the account moves to Pro/Team: protection rules then
  become a one-time settings task, and this record is superseded.

## Alternatives considered

| Alternative | Pros / cons |
|---|---|
| **Stay private on Free; merge click is the gate [chosen]** | + no cost, no visibility change; − nothing mechanical stops a red merge or a direct push except the local hook prompt |
| Make the repository public | + full branch protection, rulesets, environments for free; − the kit, its work items and decision records become public |
| Upgrade to GitHub Pro | + protection on a private repo; − recurring cost for a solo repo whose CI already reports everything |

## Links

- `docs/sdlc/spikes/pr-review-identity.md` (branch-protection checklist)
- `scripts/check_control_plane.sh`, `.github/workflows/sdlc-gate.yml`
- `.claude/hooks/production-gate.sh`, `scripts/deploy.sh`
- `knowledge/decisions/self-hooks-on.md`
