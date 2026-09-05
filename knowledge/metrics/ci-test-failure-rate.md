---
type: metric-definition
title: CI test failure rate
description: Share of completed sdlc-gate runs that failed per day, over a 30-day series with a trailing 14-point baseline, feeding the Maintain-play control-band detector.
tags: [metric, ci, western-electric, bands]
timestamp: 2026-09-02T20:00:00Z
---

# CI test failure rate

## Definition

For each day in the window, `failures / completed_runs` for the `sdlc-gate.yml` workflow's runs — a completed run is
one whose `conclusion` is set (not `in_progress` or `queued`); a failure is a conclusion of `failure`, `timed_out` or
`startup_failure` (`cancelled` is a human act and counts as completed, not failed); a day with zero completed runs
contributes no point rather than a zero or an undefined ratio. One float per day, oldest first, is what
`scripts/detect_bands.py --file` expects.

## Source

```
scripts/github_metrics.py ci_test_failure_rate --days 30 --workflow sdlc-gate.yml
```

(`monitoring/bands.yaml`, `metric: ci_test_failure_rate`, `source:`). Reads GitHub Actions workflow runs via
`gh api --paginate` (or `--from-json` for tests/offline runs); the pure function is
`ci_failure_series(runs, days)` in `scripts/github_metrics.py`. `--workflow` scopes the series to the gate workflow
so the nightly bands job and the review job do not sit in their own denominator; an adopter whose CI runs under
another file name changes that flag in `bands.yaml`.

## Baseline window

`window: 14` in `bands.yaml` — for each tested run of points, `scripts/detect_bands.py` takes the mean and σ of the 14
points that precede the run (a trailing baseline, never the run itself) and tests every point after the first 14,
reporting the highest tier seen with the index of the breaching point. `baseline: rolling_30d` names the series
span (`--days 30`). Rules: all four Western Electric rules (3σ, 2-of-3 beyond 2σ, 4-of-5 beyond 1σ, 8 in a row on
one side reported as `drift` and acted on as 1σ), as documented at the top of `detect_bands.py`. A baseline with zero
variance — thirty green days — treats any different value as beyond every band, so the first red day breaches.

## Tiers

| Tier | Action |
|---|---|
| 1σ (and `drift`) | `log` — recorded, no agent invoked. |
| 2σ | `diagnose` — Claude runs read-only with `tools: "Read,Grep,Bash(gh run view *)"` to explain the breach. |
| 3σ | `propose` — declared route: a `pull_request` or the [rollback runbook](../runbooks/rollback-deploy.md). In this phase the workflow diagnoses 3σ exactly like 2σ and files an issue; nothing acts on the route (`docs/sdlc/phase-2-roadmap.md`, autonomous Maintain). It never merges or runs either. |

See `.github/workflows/bands.yml` for the daily collect-then-detect job that invokes this; its matrix is generated
from `bands.yaml` by `scripts/bands_config.py`, so the two files cannot drift.

## Caveats

- In-progress and queued runs are excluded from both the numerator and the denominator — a day mid-run is not
  scored as if those runs had already failed.
- A day with no completed runs is omitted from the series entirely, not recorded as `0.0` (which would understate
  the baseline) or skipped as a gap (which `detect_bands.py`'s window-based baseline cannot represent) — see
  `ci_failure_series` in `scripts/github_metrics.py`.
- The detector needs at least `window + 1` (15) points before it tests anything (`tested: 0` until then) and
  `window + 8` (22) before the drift rule can fire; with the series scoped to `sdlc-gate.yml`, which runs only on
  pull requests, a quiet repo may take a few weeks to accumulate them.
- Every point after the baseline is tested, so a spike two weeks ago is reported again each night until it leaves
  the 30-day series; the workflow comments on the open `[band] ci_test_failure_rate breached` issue instead of filing
  a new one, and closing that issue ends the thread.
