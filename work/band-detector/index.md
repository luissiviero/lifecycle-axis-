---
type: sdlc/work-item
id: band-detector
title: The band detector cannot see the breach it exists for
description: A zero-variance baseline never breaches, the baseline is the first N points forever, the PR series ignores --days, one Western Electric rule is missing, and the nightly job files a duplicate issue per night.
timestamp: 2026-09-05T01:57:50Z
---
# The band detector cannot see the breach it exists for

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; A zero-variance baseline never breaches, the baseline is the first N points forever, the PR series ignores --days, one Western Electric rule is missing, and the nightly job files a duplicate issue per night.
- [spec.md](spec.md) — status: approved; approved-by: luissiviero; Requirements and design for a trailing-baseline, four-rule Western Electric detector, honest GitHub metrics, a bands.yaml-driven workflow that deduplicates its issues, and docs that match.
- [plan.md](plan.md) — status: approved; approved-by: luissiviero; Files, order, proof and risks for the trailing-baseline four-rule detector, the honest GitHub metrics, the bands.yaml-driven workflow with issue deduplication, and the docs that match.

Last gate: - 2026-09-05T02:40:00Z | PR #31 | draft -> in-review | claude | af0254f | implementation of steps 1-9 complete (plan.md stays approved); three deviations recorded in plan.md; needs control-plane-approved (bands workflow, .sdlc/active)
