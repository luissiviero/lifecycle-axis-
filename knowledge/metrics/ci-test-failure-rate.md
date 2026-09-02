---
type: metric-definition
title: CI test failure rate
description: Share of completed CI workflow runs that failed per day, over a rolling 30-day baseline, feeding the Maintain-play control-band detector.
tags: [metric, ci, western-electric, bands]
timestamp: 2026-09-02T20:00:00Z
---

# CI test failure rate

## Definition

For each day in the window, `failures / completed_runs` for the CI workflow's runs — a completed run is one whose
`status` is terminal (not `in_progress` or `queued`); a day with zero completed runs contributes no point rather than
a zero or an undefined ratio. One float per day, oldest first, is what `scripts/detect_bands.py --file` expects.

## Source

```
scripts/github_metrics.py ci_test_failure_rate --days 30
```

(`monitoring/bands.yaml`, `metric: ci_test_failure_rate`, `source:`). Reads GitHub Actions workflow runs via
`gh api --paginate` (or `--from-json` for tests/offline runs); the pure function is
`ci_failure_series(runs, days)` in `scripts/github_metrics.py`.

## Baseline window

`rolling_30d` — the first 30 points feed `scripts/detect_bands.py`'s baseline mean/σ (`--window 30`, the default);
points after that are tested against it. Rule: Western Electric, as documented at the top of `detect_bands.py`.

## Tiers

| Tier | Action |
|---|---|
| 1σ | `log` — recorded, no agent invoked. |
| 2σ | `diagnose` — Claude runs read-only with `tools: "Read,Grep,Bash(gh run view *)"` to explain the breach. |
| 3σ | `propose` — Claude opens a `pull_request` or proposes the [rollback runbook](../runbooks/rollback-deploy.md); it never merges or runs either. |

See `.github/workflows/bands.yml` for the daily collect-then-detect job that invokes this.

## Caveats

- In-progress and queued runs are excluded from both the numerator and the denominator — a day mid-run is not
  scored as if those runs had already failed.
- A day with no completed runs is omitted from the series entirely, not recorded as `0.0` (which would understate
  the baseline) or skipped as a gap (which `detect_bands.py`'s window-based baseline cannot represent) — see
  `ci_failure_series` in `scripts/github_metrics.py`.
- The detector needs at least `--window` (30) points before it will report a tier; a new or low-traffic repo may
  run for a month before the band means anything.
