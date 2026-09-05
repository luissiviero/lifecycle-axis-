---
type: sdlc/work-item
id: deploy-gate
title: The deploy path fails open; every route to production must fail closed on a named human
description: RELEASE_APPROVAL is derived from the commit it is meant to approve, the gate hook misses the gh and deploy.sh routes, deploy.sh is satisfied by three exported variables, and a release authorization file is never checked against the approvers list.
timestamp: 2026-09-04T21:50:29Z
---
# The deploy path fails open; every route to production must fail closed on a named human

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; RELEASE_APPROVAL is derived from the commit it is meant to approve, the gate hook misses the gh and deploy.sh routes, deploy.sh is satisfied by three exported variables, and a release authorization file is never checked against the approvers list.
- [spec.md](spec.md) — status: approved; approved-by: luissiviero; Requirements and design for validating release authorizations against the release-manager role, gating the gh and deploy.sh routes, and unbinding RELEASE_APPROVAL from github.sha.
- [plan.md](plan.md) — status: approved; approved-by: luissiviero; Files, order, proof and risks for validating release authorizations, gating the gh and deploy.sh routes, and unbinding RELEASE_APPROVAL from github.sha.

Last gate: - 2026-09-05T01:03:55Z | PR #27 | draft -> in-review | claude | a846ba3 | implementation of steps 1-9 complete (plan.md stays approved); six deviations recorded in plan.md; needs control-plane-approved (production-gate hook, deploy workflow, .sdlc text) and the owner's deletion of the tracked hook-decisions.log
