---
type: metric-definition
title: PR cycle time (hours)
description: Hours from PR open to merge, one value per merged PR over a 30-day series with a trailing 14-point baseline, feeding the Maintain-play control-band detector.
tags: [metric, pull-request, western-electric, bands]
timestamp: 2026-09-02T20:00:00Z
---

# PR cycle time (hours)

## Definition

Wall-clock hours from a pull request's `created_at` to its `merged_at`, one value per **merged** PR, oldest merge
first — an open or closed-unmerged PR contributes nothing. One float per line is what `scripts/detect_bands.py
--file` expects.

## Source

```
scripts/github_metrics.py pr_cycle_time_hours --days 30
```

(`monitoring/bands.yaml`, `metric: pr_cycle_time_hours`, `source:`). Reads pull requests via `gh api --paginate`
(newest-updated first; the API has no merge-date filter) or `--from-json` for tests/offline runs; the pure function is
`pr_cycle_series(prs, days)` in `scripts/github_metrics.py`, filtered to `merged_at` set and to merges within
`--days` of the latest merge in the data (measured from the data, not the wall clock, so fixtures stay reproducible).

## Baseline window

`window: 14` in `bands.yaml` — for each tested run of points, `scripts/detect_bands.py` takes the mean and σ of the 14
merges that precede the run (a trailing baseline, never the run itself) and tests every merge after the first 14,
reporting the highest tier seen with the index of the breaching point. `baseline: rolling_30d` names the series
span (`--days 30`). Rules: all four Western Electric rules (3σ, 2-of-3 beyond 2σ, 4-of-5 beyond 1σ, 8 in a row on
one side reported as `drift` and acted on as 1σ), as documented at the top of `detect_bands.py`.

## Tiers

| Tier | Action |
|---|---|
| 1σ (and `drift`) | `log` — recorded, no agent invoked. |
| 2σ | `diagnose` — Claude runs read-only with `tools: "Read,Grep"` to explain the drift. |
| 3σ | `propose` — declared route: a `report:engineering-leadership`. In this phase the workflow diagnoses 3σ exactly like 2σ and files an issue; nothing acts on the route. It does not act on the PR pipeline itself. |

See `.github/workflows/bands.yml` for the daily collect-then-detect job that invokes this; its matrix is generated
from `bands.yaml` by `scripts/bands_config.py`, so the two files cannot drift.

## Caveats

- Series is ordered by merge time, so a burst of old PRs merged together (e.g. after a freeze) reads as several
  points with the same or nearby timestamps, not as one outlier — the detector sees them as consecutive readings.
- A PR reopened and merged later is scored once, at its actual `merged_at` — the metric does not track cycle time
  across a reopen separately from the original open.
- The detector needs at least `window + 1` (15) merged PRs in the 30-day series before it tests anything
  (`tested: 0` until then) and `window + 8` (22) before the drift rule can fire; a low-merge-volume repo may take a
  while to establish a baseline.
- Every point after the baseline is tested, so an outlier merge is reported again each night until it leaves the
  30-day series; the workflow comments on the open `[band] pr_cycle_time_hours breached` issue instead of filing a
  new one, and closing that issue ends the thread.
