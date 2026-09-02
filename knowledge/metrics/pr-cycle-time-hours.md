---
type: metric-definition
title: PR cycle time (hours)
description: Hours from PR open to merge, one value per merged PR over a rolling 30-day baseline, feeding the Maintain-play control-band detector.
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

(`monitoring/bands.yaml`, `metric: pr_cycle_time_hours`, `source:`). Reads pull requests via `gh api --paginate` (or
`--from-json` for tests/offline runs); the pure function is `pr_cycle_series(prs)` in `scripts/github_metrics.py`,
filtered to `merged_at` set.

## Baseline window

`rolling_30d` — the first 30 merged-PR points feed `scripts/detect_bands.py`'s baseline mean/σ (`--window 30`);
later merges are tested against it. Rule: Western Electric, as documented at the top of `detect_bands.py`.

## Tiers

| Tier | Action |
|---|---|
| 1σ | `log` — recorded, no agent invoked. |
| 2σ | `diagnose` — Claude runs read-only with `tools: "Read,Grep"` to explain the drift. |
| 3σ | `propose` — Claude opens a `report:engineering-leadership`; it does not act on the PR pipeline itself. |

See `.github/workflows/bands.yml` for the daily collect-then-detect job that invokes this.

## Caveats

- Series is ordered by merge time, so a burst of old PRs merged together (e.g. after a freeze) reads as several
  points with the same or nearby timestamps, not as one outlier — the detector sees them as consecutive readings.
- A PR reopened and merged later is scored once, at its actual `merged_at` — the metric does not track cycle time
  across a reopen separately from the original open.
- The detector needs at least `--window` (30) merged PRs before it will report a tier; a low-merge-volume repo may
  take a while to establish a baseline.
