---
type: sdlc/work-item
id: agent-evals
title: Evals test the agent, and can go red
description: One prompt case among thirty-four, a nightly job that is green when the credential expires, fifteen hook cases whose negated assertions cannot fail, a path filter that misses half the config that steers the agent, and an approval-author check that reads prose.
timestamp: 2026-09-05T03:10:00Z
---
# Evals test the agent, and can go red

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; One prompt case among thirty-four, a nightly job that is green when the credential expires, fifteen hook cases whose negated assertions cannot fail, a path filter that misses half the config that steers the agent, and an approval-author check that reads prose.
- [spec.md](spec.md) — status: approved; approved-by: luissiviero; Requirements and design for five skill cases, a runner that can fail on a missing credential and can stage fixtures, effective negated assertions with a verify check, a complete workflow path filter, and a diff-line approval attribution.
- [plan.md](plan.md) — status: approved; approved-by: luissiviero; Files, order, proof and risks for the five skill cases, the runner's setup field and --require-claude flag, the eval-cases verify check with the fifteen fixed assertions, the workflow path filter and trust step, and the diff-line approval attribution.

Last gate: - 2026-09-05T03:40:00Z | PR #34 | draft -> in-review | claude | 6980254 | implementation of steps 1-8 complete (plan.md stays approved); four deviations recorded in plan.md; needs control-plane-approved (run_evals.sh, scripts/checks/eval-cases.sh, agent-evals workflow, .sdlc/active)
