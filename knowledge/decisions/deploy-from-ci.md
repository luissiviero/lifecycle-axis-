---
type: decision
title: Deploy only from CI via GitHub Environments
description: Deploys run only from a GitHub Actions workflow gated by a GitHub Environment's required reviewers; agents never run deploy commands, and the production-gate hook stays as defence in depth.
tags: [deploy, ci, github-environments, agents, sdlc]
timestamp: 2026-09-05T04:48:42Z
---

# Deploy only from CI via GitHub Environments

## Context

The kit needs one deploy path that holds regardless of which model (Claude Code, Gemini CLI, a
human) produced the change, and that keeps deploy credentials off every developer and agent
machine. `work/sdlc-kit-phase-1/decisions.md` Q5 weighed three alternatives:

| Alternative | Pros / cons |
|---|---|
| **Deploy only from CI using GitHub Environments with required reviewers; agents never run deploy commands; the gate hook stays as defence in depth [recommended]** | + model-neutral, uses existing GitHub features, credentials never on a dev machine; + production gate is a GitHub approval, fully logged; − agents cannot rehearse rollback locally; − dev deploys also go through CI |
| Deploy and rollback exposed as MCP tools with per-environment credentials | + the playbook's target state (allowlist, not shell); + agents can deploy to dev freely; − an MCP server per target to build and secure |
| Shell deploy commands matched by regex in the gate hook (today's scaffold) | + works now; − regexes are brittle; − credentials live wherever the shell runs |

## Decision

Deploy only from CI, gated by a GitHub Environment per target (`development`, `staging`,
`production`), each named in `.sdlc/environments.yaml` under `github_environment:`. The
`deploy` job in `.github/workflows/deploy.yml` sets `environment: ${{ inputs.environment ||
'production' }}`, so GitHub's required-reviewer gate on that Environment fires *before* the job's
steps start — no workflow code can race or bypass it.

Inside the job, `scripts/deploy.sh <environment>` is a guard, not a deployer. It refuses to run
unless all of the following hold, and otherwise prints a clear refusal and exits 1:

1. A human bound an approval to `git rev-parse HEAD`, by one of two routes: a release manager
   stored the 40-hex SHA as the Environment secret `RELEASE_APPROVAL`, or committed
   `.sdlc/release-authorizations/<sha>` whose `approved-by` holds `release-manager` in
   `.sdlc/approvers.yaml`. A set `RELEASE_APPROVAL` wins and must equal HEAD; with it empty, the
   committed file is checked and any other file refuses, naming the handle (work/deploy-gate).
2. `CI` is set — the script refuses unless it is ("deploy runs from CI only"). Any shell can export it,
   so like guard 4 it is a hint, not a gate on its own; guard 1 is the gate.
3. The requested environment exists in `.sdlc/environments.yaml` (otherwise it lists the valid
   ones).
4. For an environment whose `approval:` is `release-manager` (production today), `GITHUB_ACTIONS`
   must be `true` — a hint that the job is running inside GitHub Actions, where the Environment's
   required-reviewer gate fires before the job's steps. Any shell can export it, so it is not a
   gate on its own; guard 1 is the gate.

When every guard passes, `scripts/deploy.sh` prints `DEPLOY: would run <command> for <environment>
at <sha>` and exits 0 without executing anything — the real command is a placeholder marked
`# ADOPTERS: replace with your deploy command`, left for each adopting project to fill in.

Agents never run deploy commands. `.claude/hooks/production-gate.sh` (the `RELEASE_APPROVAL`
convention it already implements) stays as defence in depth for the disallowed case where an
agent is asked to run a deploy command inside a session anyway — it blocks unattended sessions
outright and asks a human otherwise. Required reviewers for each GitHub Environment are configured
by the repo owner in GitHub Settings → Environments, not in this repo's YAML; see the checklist in
`docs/sdlc/spikes/pr-review-identity.md`.

## Consequences

- Agents cannot run rollback locally — the `rollback:` runbook pointer in
  `.sdlc/environments.yaml` names a manual `workflow_dispatch` of the previous SHA from CI
  (`knowledge/runbooks/rollback-deploy.md`); nothing rehearses it on a schedule.
- Even `development` deploys go through CI, trading a little iteration speed for one deploy path
  that behaves the same for every environment and every producing model.
- `scripts/deploy.sh` is deliberately inert (a guard plus a placeholder echo) until an adopter
  wires in a real deploy command; `scripts/test_deploy_guard.py` locks in the guard behaviour so
  that wiring-in a real command cannot silently drop a check.
- The gate hook regex approach from the scaffold is retired as the primary control and kept only
  as defence in depth, addressing its brittleness without removing the safety net.

## Links

- `.github/workflows/deploy.yml`
- `scripts/deploy.sh`
- `.sdlc/environments.yaml`
- `scripts/test_deploy_guard.py`
- `evals/cases/deploy-refuses-without-approval.yaml`
- `.claude/hooks/production-gate.sh`
- `docs/sdlc/spikes/pr-review-identity.md`
- `work/sdlc-kit-phase-1/decisions.md`
