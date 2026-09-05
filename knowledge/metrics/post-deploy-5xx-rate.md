---
type: metric-definition
title: Post-deploy 5xx rate
description: Server-error rate in the window after a deploy, over a rolling 14-day baseline; inert until a metrics store exists to source it from.
tags: [metric, deploy, western-electric, bands]
timestamp: 2026-09-05T04:48:42Z
---

# Post-deploy 5xx rate

## Definition

Share of requests returning a 5xx status in the window immediately following a deploy to an environment, intended
as one float per window, oldest first, matching the shape `scripts/detect_bands.py --file` expects for the other
two metrics.

## Source

```
(none — no metrics store yet; tier actions are inert until one exists, see decisions.md Q7)
```

(`monitoring/bands.yaml`, `metric: post_deploy_5xx_rate`, `source:`, verbatim). Unlike `ci_test_failure_rate` and
`pr_cycle_time_hours`, this metric has no producing command today — `scripts/github_metrics.py` covers only what the
GitHub API exposes, and request-level error rates live in an application metrics store (e.g. a
logs/metrics backend) this kit does not stand up. `work/sdlc-kit-phase-1/decisions.md` Q7 records the choice to
start with GitHub-only metrics and leave this one inert rather than invent a fake source.

## Baseline window

`rolling_14d` — shorter than the other two metrics' 30-day window because a deploy-triggered metric is judged
against recent deploys, not a full month; once a real source exists, wire it through `scripts/detect_bands.py
--file --window 14` (or the equivalent `--series` length) the same way the other two metrics are. Rule: Western
Electric, as documented at the top of `detect_bands.py`.

## Tiers

| Tier | Action |
|---|---|
| 1σ | `log` — recorded, no agent invoked. |
| 2σ | `diagnose` — Claude runs read-only with `tools: "Read,Grep,Bash(kubectl logs *)"` to explain the spike. |
| 3σ | `propose` — declared route: Claude would propose the [rollback runbook](../runbooks/rollback-deploy.md) and never run it; the metric has no source yet, so nothing runs. |

See `.github/workflows/bands.yml` for the daily collect-then-detect job this metric will join once it has a source.

## Caveats

- **No source yet.** Until an adopter wires this metric to a real store, the tier actions above are aspirational —
  `bands.yml` has nothing to feed this metric and will not invoke them for it.
- Once a source exists, the same in-progress-run exclusion that applies to `ci_test_failure_rate` should apply here:
  a deploy still inside its post-deploy observation window should not be scored yet, to avoid an incomplete window
  reading as a false breach.
