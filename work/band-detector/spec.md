---
type: sdlc/spec
id: band-detector
title: The band detector cannot see the breach it exists for
description: Requirements and design for a trailing-baseline, four-rule Western Electric detector, honest GitHub metrics, a bands.yaml-driven workflow that deduplicates its issues, and docs that match.
stage: design
status: in-review
reads: intent.md
approved-by:
approved-on:
skills-applied: [security-standards]
skills-version: 60ab0f5
prompt: "Transcribed from the approved 2026-09-04 implementation plan (docs/sdlc/handoff/PLAN.md on branch claude/session-handoff), section WI-7, with the detector redesign prototyped against the existing tests before writing; reviewed by the orchestrator."
record:
resource: https://claude.ai/code/session_01Te8oN2GdvRupSixH4kjR8Y
tags: [maintain, bands, detector, western-electric, metrics, ci, consensus-item-6]
timestamp: 2026-09-05T01:57:50Z
---
# Spec: the band detector cannot see the breach it exists for

## Requirements (each maps to an intent outcome)
Intent outcomes: (1) flat baseline then spike breaches; (2) trailing baseline, full scan, highest tier; (3) four
rules with `drift`; (4) bad input exits 2; (5) honest metrics; (6) workflow driven by `bands.yaml`, deduplicated,
series kept; (7) docs match and the suite is green.

| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R-1 | A zero-variance baseline treats any point not equal to the mean as beyond every band: `[0]*30 + [1]` with `--window 14` (and with the default window) reports `3sigma`, exit 3 | 1 | `scripts/test_detect_bands.py::DetectBands::test_flat_baseline_then_spike`; eval `evals/cases/bands-detects-spike-after-flat-baseline.yaml` |
| R-2 | For a rule with run length `of` ending at index `i` (with `i - of + 1 >= window`), the baseline is the `window` points before the run; every index from `window` to the end is tested; the result is the highest tier seen with `index` of the breaching point; the five existing cases pass unchanged | 2 | `::test_earlier_three_sigma_in_tail_is_reported` (`BASE + [13, 10, 10, 10]` → `3sigma`, `index` 10), `::test_baseline_trails_the_tested_run` (`[0]*14 + [5]*15` → `3sigma` at `index` 14), the five existing tests |
| R-3 | A downward breach is reported with `side: -1` | 2 | `::test_downward_breach` (`BASE + [10, 7]` → `3sigma`, `side` -1) |
| R-4 | Eight consecutive points on one side of the baseline mean report `tier: drift`, `acts_as: 1sigma`, exit 3; seven do not | 3 | `::test_drift_eight_on_one_side` (`BASE + [10.2]*8`), `::test_seven_on_one_side_is_not_drift` (`BASE + [10.2]*7` → `None`) |
| R-5 | `--window` < 2, a NaN/inf value or a non-numeric token prints one `detect_bands: …` line on stderr and exits 2; stdout is empty; no traceback | 4 | `::DetectBandsCli::test_window_below_two_exits_2`, `::test_nan_exits_2`, `::test_non_numeric_exits_2` (subprocess; assert `Traceback` not in stderr) |
| R-6 | `pr_cycle_series(prs, days)` keeps merges within `days` of the latest merge in the data; the pulls path carries `sort=updated&direction=desc`; `timed_out` and `startup_failure` count as failures; the end-to-end tests assert the exact tier and exit code | 5 | `scripts/test_github_metrics.py::PrCycleSeries::test_days_window_trims_older_merges` (`days=1` → `[174.0]`, `days=4` → `[48.0, 174.0]`), `::CiFailureSeries::test_timed_out_and_startup_failure_count_as_failures`, `::ApiPaths::test_pulls_path_sorted_by_updated_desc`, `::EndToEndThroughDetectBands::*` assert `returncode == 0` and `tier is None` |
| R-7 | `python3 scripts/bands_config.py` prints `{"include": [{"metric", "source", "tools", "window"}, …]}` for every metric whose `source` starts with `scripts/github_metrics.py`, reading `window` and the 2σ `tools` from `monitoring/bands.yaml`; a listed metric without an integer `window` ≥ 2 exits 2; `bands.yml` builds its matrix from that output and passes `--window ${{ matrix.window }}` | 6 | `scripts/test_bands_config.py::BandsConfig::test_real_file_yields_two_github_metrics` (both `window` 14, `ci_test_failure_rate` source ends `--workflow sdlc-gate.yml`), `::test_non_github_source_is_excluded`, `::test_missing_window_exits_2`, `::test_window_below_two_exits_2`, `::BandsWorkflow::test_matrix_comes_from_config` (workflow text contains `fromJSON(needs.config.outputs.matrix)` and `--window ${{ matrix.window }}`; contains no `metric: ci_test_failure_rate` line) |
| R-8 | Before filing, the workflow looks for an open issue whose title starts with `[band] <metric> breached` and comments on it instead; the series file is uploaded as a run artifact with `actions/upload-artifact` pinned by SHA; the prompt no longer says "recent commits" | 6 | `::BandsWorkflow::test_dedupes_open_issue` (`gh issue list` and `gh issue comment` present in both issue steps), `::test_uploads_series_artifact` (`actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02`), `::test_prompt_asks_only_what_tools_allow` (`recent commits` absent); `scripts/checks/workflow-yaml.sh` and `workflow-permissions.sh` pass |
| R-9 | The metric docs, README rows 38/83/86/106, `metrics.md:11,27` and `rules/20-verifying.md:17` describe window 14, trailing baseline, four rules, failure conclusions, the `sdlc-gate.yml` scope and "3σ diagnoses only in this phase" | 7 | `grep -c 'first 30' knowledge/metrics/ci-test-failure-rate.md knowledge/metrics/pr-cycle-time-hours.md` prints `0` for each; `grep -c 'opens a .pull_request' knowledge/metrics/ci-test-failure-rate.md` prints `0`; `python3 scripts/check_okf.py` ends `OKF: N docs, 0 warnings`; `scripts/checks/context-drift.sh` clean after regeneration |
| R-10 | Whole suite green | 7 | `scripts/verify.sh` ends `VERIFY: PASS (<sha>)`; `scripts/run_evals.sh` ends `EVALS: N pass, 0 fail, N skipped`; `python3 scripts/check_artifact_chain.py --base origin/main --slug band-detector` ends `CHAIN: PASS` |

## Design
### Architecture / data flow
Unchanged shape, three stages: **collect** (`github_metrics.py` prints one float per line, oldest first),
**detect** (`detect_bands.py` prints one JSON object and exits 0 or 3), **act** (`bands.yml` maps the tier to
an issue). Two things move: the single source of metric configuration becomes `monitoring/bands.yaml`, read by
a new stdlib script `bands_config.py` in a first workflow job whose output is the matrix of the second; and
the detector scans the whole series against a trailing baseline instead of testing the last point against the
first `window` points.

### Interfaces (APIs, events, schemas) — exact shapes
`scripts/detect_bands.py` (replaces `side()`, `detect()`; `stats()` and the CLI flags are unchanged; the
default `--window` stays 30):
```python
RANK = {None: 0, "drift": 1, "1sigma": 2, "2sigma": 3, "3sigma": 4}
RULES = (  # (k sigma, points needed, run length, tier, description)
    (3, 1, 1, "3sigma", "one point beyond 3 sigma"),
    (2, 2, 3, "2sigma", "two of three beyond 2 sigma on one side"),
    (1, 4, 5, "1sigma", "four of five beyond 1 sigma on one side"),
    (0, 8, 8, "drift", "eight consecutive on one side of the mean"),
)

def side(x, m, s, k):
    if s == 0:
        return 0 if x == m else (1 if x > m else -1)
    if x > m + k * s: return 1
    if x < m - k * s: return -1
    return 0

def test_point(series, i, window):
    for k, need, of, tier, rule in RULES:
        start = i - of + 1
        if start < window: continue
        m, s = stats(series[start - window:start])
        run = series[start:i + 1]
        for sgn in (1, -1):
            if sum(1 for y in run if side(y, m, s, k) == sgn) >= need:
                r = {"tier": tier, "mean": m, "sd": s, "value": series[i], "index": i, "side": sgn, "rule": rule}
                if tier == "drift": r["acts_as"] = "1sigma"
                return r
    return None

def detect(series, window):
    if window < 2: raise ValueError("--window must be at least 2 (a baseline needs two points)")
    if any(math.isnan(x) or math.isinf(x) for x in series): raise ValueError("series contains a non-finite value")
    if len(series) <= window: return {"tier": None, "reason": "not enough points beyond baseline window", "tested": 0}
    best = None
    for i in range(window, len(series)):
        r = test_point(series, i, window)
        if r and RANK[r["tier"]] > RANK[best["tier"] if best else None]: best = r
    if best is None:
        m, s = stats(series[-window - 1:-1])
        return {"tier": None, "mean": m, "sd": s, "value": series[-1], "tested": len(series) - window}
    best["tested"] = len(series) - window
    return best
```
`main()` wraps parsing and `detect()` in one `try` and on `ValueError` prints `detect_bands: <message>` to
stderr and exits 2. Output keys the workflow reads: `tier` (unchanged). New keys: `index`, `rule`, `tested`,
`acts_as` (drift only). Exit codes: 0 no tier, 2 bad input, 3 any tier including `drift`.

Prototyped numbers (population σ): with `BASE = [10, 11, 9, 10, 10, 11, 9, 10, 10, 10]` (mean 10, σ 0.632) and
window 10: `BASE + [10, 13]` → `3sigma`; `BASE + [11.5, 10, 11.5]` → `2sigma`; `BASE + [10.8, 10.8, 10, 10.8,
10.8]` → `1sigma`; `BASE + [10.2]*8` → `drift` (10.2 is within 1σ, above the mean); `BASE + [10, 7]` →
`3sigma`, side -1; `BASE + [13, 10, 10, 10]` → `3sigma`, index 10; `[0]*30 + [1]` with window 14 → `3sigma`,
mean 0, sd 0, index 30, tested 17.

`scripts/github_metrics.py`:
- `FAILURE_CONCLUSIONS = {"failure", "timed_out", "startup_failure"}`; `ci_failure_series` counts a run as a
  failure when `conclusion in FAILURE_CONCLUSIONS` (`:104`). `cancelled` stays in the denominator only.
- `pr_cycle_series(prs, days)`: after sorting by `merged_at`, keep rows whose merge date is on or after
  `latest_merge_date - (max(days, 1) - 1)` days, the same convention as `ci_failure_series` (measured from the
  data, not the wall clock, so fixtures stay reproducible). The CLI passes `a.days` (`:164`).
- `_api_path(metric, repo, days, workflow)` returns the request path; for pulls:
  `repos/{repo}/pulls?state=closed&per_page=100&sort=updated&direction=desc` (`:158`). The runs paths are
  unchanged apart from moving into the function.

`scripts/bands_config.py` (new, stdlib): `parse(text) -> list[dict]` reads the `metrics:` list of
`monitoring/bands.yaml` in the shape the file has (one `- metric:` item per entry, one-line scalar values,
`tiers:` as a mapping of flow mappings `{ action: …, tools: "…" }`, `#` comments, blank lines) and raises
`ValueError` on any other line; `matrix(metrics) -> list[dict]` keeps entries whose `source` starts with
`scripts/github_metrics.py` and returns `{"metric", "source", "tools", "window"}` with `tools` from the 2σ
tier (empty string if none) and `window` as an int, raising `ValueError` when `window` is missing or below 2;
`main()` prints `json.dumps({"include": rows})` on one line and exits 0, or prints `bands_config: <message>`
to stderr and exits 2 (`--file` defaults to `monitoring/bands.yaml`).

`monitoring/bands.yaml`: line 5 becomes `source: "scripts/github_metrics.py ci_test_failure_rate --days 30
--workflow sdlc-gate.yml"`; line 13's pointer becomes `see work/sdlc-kit-phase-1/decisions.md Q7`; every metric
gains `window: 14` after its `rules:` line (the detector's trailing baseline; `baseline: rolling_30d` keeps
naming the fetch span).

`.github/workflows/bands.yml`:
- New first job `config` (`runs-on: ubuntu-latest`, checkout pinned as today, `outputs.matrix`): runs
  `python3 scripts/bands_config.py` and writes `matrix=<json>` to `$GITHUB_OUTPUT`.
- Job `detect` gains `needs: config` and `strategy.matrix: ${{ fromJSON(needs.config.outputs.matrix) }}`; the
  hard-coded `include:` block (`:35-42`) is deleted; the detect step runs
  `--window ${{ matrix.window }}` (`:61`).
- After the collect step: `uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4.6.2`
  with `name: bands-series-${{ matrix.metric }}` and `path: monitoring/series/${{ matrix.metric }}.txt`.
- New step `Find open band issue` (`id: existing`, `GH_TOKEN`): `gh issue list --state open --limit 50
  --json number,title` filtered with `--jq` to the first title starting with `[band] <metric> breached`;
  writes `number=<n or empty>` to `$GITHUB_OUTPUT`.
- Both issue steps: when `steps.existing.outputs.number` is non-empty, `gh issue comment <n> --body-file
  <file>` with a first line `Still breached (<tier>) on <date>, index <n> of the series.`; otherwise
  `gh issue create` as today. Title format unchanged: `[band] <metric> breached <tier>`.
- The prompt line 91 becomes `Diagnose read-only: look at the workflow runs and the series in
  monitoring/series/$METRIC.txt.`
- `permissions` unchanged (`contents: read`, `issues: write`, `actions: read`); no PR is ever opened.

`evals/cases/bands-detects-spike-after-flat-baseline.yaml` (`kind: hook`): `check` runs the detector on
thirty zeros and a one with `--window 14`, asserts exit 3 and `"tier": "3sigma"` in stdout; runs it with
`--window 1`, asserts exit 2 and empty stdout; runs `python3 scripts/bands_config.py` and asserts both metric
names and `"window": 14` in its output.

### Data and migrations
None. `monitoring/series/*.txt` is a run artifact (retention: the repository default), never committed.

### Failure modes and how they surface
- `bands.yaml` changes shape: `bands_config.py` exits 2 with the offending line; the `config` job fails and no
  metric runs (fail closed, visible in the Actions tab).
- A metric lacks `window`: exit 2, same route; `test_bands_config.py` pins the real file.
- The source command fails (no `gh`, API error): the collect step fails the job, as today; no artifact, no issue.
- Series shorter than `window + 1`: `tier: null`, exit 0, `tested: 0`; the drift rule needs `window + 8` points.
- Non-numeric series (a source printing an error to stdout): exit 2, one line, the step fails loudly instead
  of `breach=1` from a traceback.
- Issue search misses (title edited by hand): one duplicate issue, as today; the title format is pinned by test.

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: `bands.yaml`'s 3σ `propose` routes (`pull_request`, `runbook:rollback-deploy`, `report:engineering-leadership`) are read by nothing; the workflow diagnoses at 2σ and 3σ alike — policy: docs say what the code does (consensus) — contradiction? no — owner: luissiviero — resolution: keep the routes as the declared intent, and say in the docs that 3σ diagnoses only in this phase; the roadmap already defers autonomous Maintain.
- C2: a full-series scan re-reports an old spike every night for up to 30 days — policy: Maintain play, "no duplicate work for the on-call" — contradiction? no — owner: luissiviero — resolution: the comment lands on the one open issue and carries `index`; closing the issue ends the thread; the next night files a new issue only if the breach is still in the series.
- C3: a hand-written YAML subset parser can drift from the file it reads — policy: security-standards §3 (validate at the boundary, fail closed) — contradiction? no — owner: luissiviero — resolution: the parser refuses any line it does not understand and the test parses the real file; PyYAML is not required because `verify.sh` must run where it is absent (`workflow-yaml.sh` makes the same choice).
- C4: `ci_test_failure_rate` scoped to `sdlc-gate.yml` is right for this repo and wrong for an adopter with a different CI workflow — policy: adopter's first hour — contradiction? no — owner: luissiviero — resolution: the metric doc's Source section says to change `--workflow` in `bands.yaml`; `adopter-first-hour` copies `bands_config.py`.
- C5: the diagnosis step runs Claude with `GH_TOKEN` (issues: write) and the tier's tools — policy: security-standards §7 (least privilege for automation) — contradiction? no — owner: luissiviero — resolution: unchanged tool list; the prompt no longer asks for data the tools cannot reach; the issue is filed by the workflow, not by Claude.

## Open questions carried from intent.md
- `drift` as its own tier name with `acts_as: 1sigma`? (proposed yes)
- `window: 14` per metric in `bands.yaml`, `baseline: rolling_30d` kept as the fetch span? (proposed yes)
- Drop "recent commits" from the prompt rather than granting `git log`? (proposed drop)
- Accept nightly comments on the one open issue while an old spike is still in the series? (proposed yes)

## Decisions (ADR-style: context → decision → consequences)
- D1: The baseline for a run rule is the `window` points before the run, not before its last point: a baseline that slides under the run absorbs a sustained shift, and the existing four-of-five case went undetected in the first prototype → the run never estimates its own limits; the five existing tests pass unchanged; a rule with run length `of` needs `window + of` points.
- D2: Scan every point after the first `window` and report the highest tier: the nightly schedule can miss a night, and the last-point test hid every earlier spike → an old breach is re-reported until it leaves the series (C2); `index` and `tested` say where and how much was scanned.
- D3: `drift` is its own tier name: `bands.yaml` tiers stay `1sigma|2sigma|3sigma` and the workflow's `if:` lines are untouched (a `drift` tier is neither 2σ nor 3σ, so it logs like 1σ) → `acts_as: 1sigma` in the JSON tells a reader the mapping; exit 3 as for every tier.
- D4: `bands_config.py` is stdlib and shape-specific rather than a PyYAML load: `verify.sh` and the unit suite must run where PyYAML is absent, and a strict parser fails loudly on drift (C3) → adopters editing `bands.yaml` keep its current shape; the parser's error names the line.
- D5: The prompt loses "recent commits" instead of the tools gaining `Bash(git log *)`: least privilege; the runs and the series are what the 2σ tools can already reach → the diagnosis is narrower and honest about it.
- D6: The PR window is measured from the latest merge in the data, like the CI series from its latest bucket: pure functions stay fixture-reproducible → a repo with no merge in 30 days still reports its last window rather than nothing; the CLI's `since` is not applied to pulls (the API has no `merged>=` filter), so the sort order only brings recent PRs first.
- D7: `actions/upload-artifact` pinned to the SHA of v4.6.2 (`ea165f8d…`), the newest v4 tag at drafting time: every action in this repo is SHA-pinned with a version comment → Dependabot keeps it current like the checkout pin.

## Gotchas found while reading the codebase
- `test_detect_bands.py:15` (`BASE + [10.8, 10.8, 10, 10.8, 10.8]`) fails under a naive trailing baseline (baseline ending at `i - 1`): the run raises the mean to 10.32 and σ to 0.44 and only two points clear 1σ. D1 exists because of this case.
- `bands.yml:23-28` sets `HAVE_CLAUDE_AUTH` at job level for the `detect` job; the new `config` job needs no secrets and must not copy that block (`workflow-permissions.sh` does not care, but the secret would be exposed to a job that does not need it).
- `bands.yml:65` extracts `tier` with `python3 -c`, so the runner already has Python 3; `bands_config.py` adds no setup step.
- `run_evals.sh:33-37` reads a `check: |` block until the first non-indented line; the eval's shell must be indented throughout.
- `github_metrics.py:152` computes `since` only for runs; pulls have no server-side merge filter, hence D6.
- `ci_failure_series` already omits days with zero completed runs; scoping to `sdlc-gate.yml` (which runs on `pull_request` only) makes quiet days more common, so a 30-day series may hold fewer than 15 points early on and the detector reports `tested: 0`, exit 0.
- `docs/sdlc/rules/20-verifying.md:17` is rendered into `CLAUDE.md:40`, `GEMINI.md` and `AGENTS.md`; the context files change in this item and must be regenerated before commit or `context-drift.sh` fails `verify.sh`.
- The chain check's in-progress mode covers a PR that touches only `work/band-detector/` and `work/index.md`; the implementation PR is the same PR, so every path above must be in the plan's file list, `.sdlc/active` included.

## Not doing
- A metrics store or any source for `post_deploy_5xx_rate`; its entry keeps `source: (none …)` and is excluded from the matrix by `bands_config.py`.
- The 3σ `propose` route (PR, runbook, report): the workflow keeps filing issues only (C1).
- Changing the CLI default `--window` (30): `bands.yaml` carries 14 and the workflow passes it.
- Treating `cancelled` runs as failures or removing them from the denominator.
- The roadmap note at `docs/sdlc/phase-2-roadmap.md:116-117` (`docs-reconcile`).
