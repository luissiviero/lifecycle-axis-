---
type: sdlc/intent
id: band-detector
title: The band detector cannot see the breach it exists for
description: A zero-variance baseline never breaches, the baseline is the first N points forever, the PR series ignores --days, one Western Electric rule is missing, and the nightly job files a duplicate issue per night.
stage: plan
status: in-review
author: Luis Siviero (repo owner), drafted with Claude from the 2026-09-04 consensus list (item 6)
approved-by:
approved-on:
supersedes:
record:
resource: https://claude.ai/code/session_01Te8oN2GdvRupSixH4kjR8Y
tags: [maintain, bands, detector, western-electric, metrics, ci, consensus-item-6]
timestamp: 2026-09-05T01:57:50Z
---
# Intent: the band detector cannot see the breach it exists for

## Problem
The Maintain play rests on a deterministic detector (`docs/sdlc/README.md:38`): mean and σ over a rolling
window, Western Electric rules, a tier that bounds what Claude may do. The code does not deliver that; seven
facts, each verified in the working tree (consensus item 6):

1. `scripts/detect_bands.py:20`: `if s == 0: return 0`. A baseline with zero variance never breaches. Thirty
   days of green CI is exactly that baseline, so the first 100%-failure day returns `tier: null`, exit 0. No
   test uses a constant baseline.
2. `detect_bands.py:27`: the baseline is `series[:window]`, the *first* N points, not a rolling window; only the
   last point is tested for 3σ (`:29-30`) and only the last three or five for the run rules (`:32`). A spike
   two nights ago that the schedule missed is never seen.
3. `scripts/github_metrics.py:116-129`: `pr_cycle_series(prs)` takes no date argument and `:158` fetches every
   closed PR with no filter, so `--days` is ignored for `pr_cycle_time_hours` and the baseline is the repo's
   first merges forever. `monitoring/bands.yaml:21` and `knowledge/metrics/pr-cycle-time-hours.md:29` say
   `rolling_30d`.
4. `.github/workflows/bands.yml:61` runs `--window 14`; the metric docs (`ci-test-failure-rate.md:29,49`,
   `pr-cycle-time-hours.md:29,48`) say 30 and "needs at least 30 points". With window 30 and a 30-day series
   the detector would test nothing.
5. Three of the four Western Electric rules: the eight-consecutive-on-one-side drift rule is absent, and the
   playbook's reason for the rules is slow drift as well as spikes.
6. `bands.yml:105` and `:130` run `gh issue create` unconditionally, so a multi-day breach files one duplicate
   issue per night; the diagnosis prompt (`:91`) asks Claude to look at "recent commits" while `git log` is
   not in the allowed tools; the matrix (`:35-42`) hard-copies `bands.yaml`'s `source:` and `tools:` so the
   two files can drift; the collected series is discarded with the runner.
7. `github_metrics.py:104` counts only `conclusion == "failure"`: `timed_out` and `startup_failure` runs read
   as passes; and with no `--workflow`, `ci_test_failure_rate` counts every workflow in the repo, including
   the nightly bands job and the review job, in its own denominator. A non-numeric series or `--window 0`
   ends in a traceback rather than a message.

## Proposed outcome
1. A flat baseline followed by a spike breaches: `python3 scripts/detect_bands.py --series <30 zeros>,1` prints
   `"tier": "3sigma"` and exits 3.
2. The baseline for each tested run is the `window` points that precede it; every point after the first
   `window` is tested and the highest tier seen is reported, with the index of the breaching point.
3. All four Western Electric rules; the drift rule reports `tier: drift` and acts as the 1σ tier (`log`).
4. `--window` below 2, a non-numeric value or NaN exits 2 with one line on stderr; never a traceback.
5. `pr_cycle_time_hours` honours `--days`; `timed_out` and `startup_failure` count as failures;
   `ci_test_failure_rate` is scoped to `sdlc-gate.yml` in `bands.yaml`.
6. `bands.yml` builds its matrix and `--window` from `monitoring/bands.yaml` (one source), comments on an
   existing open `[band] <metric> breached` issue instead of filing a new one, uploads the series as a run
   artifact, and asks only for what the tools allow.
7. The metric docs, README rows, `metrics.md` and the verifying rule say what the code does: window 14,
   trailing, 3σ diagnoses only in this phase. Tests and an eval pin every item above; `verify.sh`, the chain
   check, the evals and the OKF check are green.

## Affected users and systems
- Users: the owner (reads the nightly issue); an adopter who points `bands.yaml` at a real metric.
- Services / repos / data: `scripts/detect_bands.py`, `scripts/github_metrics.py`, a new
  `scripts/bands_config.py`, `monitoring/bands.yaml`, `.github/workflows/bands.yml`, the two metric docs,
  `docs/sdlc/README.md`, `docs/sdlc/metrics.md`, `docs/sdlc/rules/20-verifying.md` (and the generated
  context files).

## Constraints
- Must: stay deterministic and stdlib-only (no model, no PyYAML dependency in the workflow or in `verify.sh`);
  keep the five existing `test_detect_bands.py` cases passing unchanged; keep the JSON keys the workflow
  reads (`tier`) and the exit codes 0 / 3; keep the workflow read-only apart from issues (no
  `contents: write`, no PR).
- Must not: open a pull request from the workflow; grant the diagnosis step tools beyond the tier's list;
  edit `scripts/verify.sh`, `scripts/run_tests.py`, `scripts/run_evals.sh`, `scripts/checks/`, or `.sdlc/`
  beyond `.sdlc/active`.
- Out of scope: a metrics store for `post_deploy_5xx_rate`; the 3σ `propose` route (PR or runbook) stays
  unimplemented and is now documented as such; `cancelled` runs (a human act) keep their current treatment;
  the roadmap line (`docs/sdlc/phase-2-roadmap.md:116-117`) is `docs-reconcile`'s.

## Risk class
low — nothing runs in production; the workflow only files or comments on issues; a wrong detector verdict costs
one nightly issue or one missed night, and every rule is pinned by a unit test with hand-checkable numbers.
Product owner approves intent and spec; tech lead approves the plan (same person here).

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: Report the drift rule as its own tier name (`drift`, with `acts_as: 1sigma` in the JSON) rather than as
  `1sigma`, so a reader can tell a slow drift from a four-of-five run?
  A: (proposed yes)
- Q: Set `window: 14` per metric in `bands.yaml` next to `baseline: rolling_30d` (the fetch span stays 30
  days; the detector's baseline is the trailing 14 points)?
  A: (proposed yes)
- Q: Drop "recent commits" from the diagnosis prompt rather than adding `Bash(git log *)` to the 2σ tools?
  A: (proposed drop the words; least privilege)
- Q: Accept that a full-series scan re-reports an old spike every night until it leaves the 30-day series,
  as a comment on the one open issue?
  A: (proposed yes; the comment carries the breach index, and a closed issue stops the comments)
