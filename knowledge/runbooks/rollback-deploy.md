---
type: runbook
title: Roll back a deploy
description: The pre-approved rollback for a breached control band or a bad deploy — an agent may only propose it, a human runs it.
tags: [runbook, deploy, rollback, production-gate]
timestamp: 2026-09-02T20:00:00Z
---

# Roll back a deploy

Referenced by `monitoring/bands.yaml` (`ci_test_failure_rate` and `post_deploy_5xx_rate`, 3σ tier: `routes:
[runbook:rollback-deploy]`) and by `.sdlc/environments.yaml` (`production.rollback: runbook:rollback-deploy`,
"rehearsed in staging on a schedule"). See [`deploy-from-ci.md`](../decisions/deploy-from-ci.md) for why deploy and
rollback both run only from CI.

## Preconditions

- A deploy is inside the breach window: the control band on `ci_test_failure_rate` or `post_deploy_5xx_rate`
  breached 3σ (per `monitoring/bands.yaml`) at or after the last deploy to the affected environment, and no rollback
  for that deploy has completed yet.
- The previous release tag (the one deployed immediately before the breaching deploy) is known and still exists.

## Steps

1. Open the `workflow_dispatch` form for `.github/workflows/deploy.yml` and set `environment` to the affected
   environment and `sha` to the previous release's 40-hex commit SHA (`git rev-list -n 1 <tag>`) — the last
   known-good release, not the breaching one. `sha` is the only ref input the form has.
2. The required reviewer for that environment's GitHub Environment (`.sdlc/environments.yaml`,
   `github_environment:`) approves the run. For `production` this is the `release-manager` role in
   `.sdlc/approvers.yaml`.
3. The release manager binds the approval to that same 40-hex SHA: store it as the Environment secret
   `RELEASE_APPROVAL` (Settings -> Environments -> the environment -> secrets), or commit
   `.sdlc/release-authorizations/<sha>` with `approved-by: <release-manager handle>`. `scripts/deploy.sh` refuses
   without one of the two — see `.claude/hooks/production-gate.sh` for the same convention enforced
   defence-in-depth inside an agent session.
4. The run deploys the previous release tag through the normal `deploy.yml` path — there is no separate rollback
   command; a rollback is a forward deploy of the last known-good SHA.

## Verification

The metric that breached (`ci_test_failure_rate` or `post_deploy_5xx_rate`) returns to inside its baseline band —
compare the next reading from the metric's `source` command (see `knowledge/metrics/`) against the `baseline` window
recorded there — before the incident is closed.

## Rule: propose, never run

An agent may only *propose* this runbook: open the `workflow_dispatch` link above (or, equivalently, open a PR that
changes the release tag) and hand it to a human. An agent never triggers the run, never approves the GitHub
Environment gate, and never sets `RELEASE_APPROVAL` itself. This mirrors `.claude/hooks/production-gate.sh`, which
blocks a deploy-shaped command outright in an unattended session and otherwise asks a human, and
[`deploy-from-ci.md`](../decisions/deploy-from-ci.md)'s decision that deploy (and therefore rollback, which is just
another deploy) runs only from CI under a GitHub Environment's required reviewers.
