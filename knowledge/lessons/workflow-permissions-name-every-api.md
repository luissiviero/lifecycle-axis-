---
type: lesson
title: A workflow's permissions block names every API surface its scripts touch
description: "bands.yml granted actions: read for the runs endpoint and nothing for pulls, so one matrix job returned HTTP 403 on every run for three days while the other two passed and hid it."
tags: [lesson, workflows, permissions, github-actions, bands]
resource: ../../.github/workflows/bands.yml
timestamp: 2026-09-05T07:15:00Z
---
# A workflow's permissions block names every API surface its scripts touch

## What happened
`.github/workflows/bands.yml` shipped in `work/band-detector` with `contents: read`, `issues: write` and
`actions: read`. Its detector fans out one job per metric, and `scripts/github_metrics.py` reads two
different endpoints: `repos/<repo>/actions/runs` for `ci_test_failure_rate`, which `actions: read` covers,
and `repos/<repo>/pulls` for `pr_cycle_time_hours`, which nothing covered. That job died on its first step
with `gh: Resource not accessible by integration (HTTP 403)` on every run, scheduled and manual alike, from
the day the workflow merged.

Two things kept it hidden. The other two jobs passed, so the run was red without looking like a permission
problem, and a red matrix reads as "the detector is unhappy" rather than "one job never started". And the
metric it killed was the one nobody was watching: the series was never collected, so there was no gap in a
chart to notice, just an absence.

It surfaced only when the owner ran the workflow by hand and someone read the job log. Adding
`pull-requests: read` fixed it in one line. The first green run then detected a 3σ breach, diagnosed it and
filed an issue — the entire Maintain path had never once executed.

## Rule
When a workflow's scripts call an API, the `permissions:` block names every surface they touch, not only the
one that was in mind when the block was written. Adding a metric, a script or a step that reaches the API
means checking its endpoints against that block in the same change. A red job whose first step failed is a
permission problem until proven otherwise; read the log before assuming the logic is wrong.

## Where it is enforced
Nothing enforces it. `scripts/checks/workflow-permissions.sh` refuses `contents: write` outside its
allowlist and requires every workflow to declare a block, but it cannot know which endpoints a script will
call, so a too-narrow grant passes every check and fails only at runtime. The job log's 403 is the whole
signal. This is prose, and it is why the rule says to check at the moment of writing.
