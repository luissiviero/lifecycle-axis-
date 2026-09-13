#!/usr/bin/env python3
"""GitHub-only metrics producer for the Maintain-play control-band detector (T18).

No metrics store required: everything comes straight from the GitHub API via `gh api --paginate`,
or from a saved API response for tests and offline runs. Output is one float per line, oldest
first — exactly the shape `scripts/detect_bands.py --file` accepts.

Usage:
  github_metrics.py ci_test_failure_rate  [--repo owner/name] [--days N=30] [--from-json PATH] [--workflow NAME]
  github_metrics.py pr_cycle_time_hours   [--repo owner/name] [--days N=30] [--from-json PATH]
  github_metrics.py actions_minutes_per_pr [--repo owner/name] [--days N=30] [--from-json PATH] [--default-branch B]

Metrics:
  ci_test_failure_rate  -- per-day failures/completed-runs for the workflow runs endpoint; a run
                           whose conclusion is failure, timed_out or startup_failure is a failure.
  pr_cycle_time_hours   -- hours from PR open to merge, one value per merged PR, oldest first,
                           keeping the merges within --days of the latest merge in the data.
  actions_minutes_per_pr -- per-day billed Actions minutes divided by the pull requests paying
                           for them; excludes schedule and workflow_dispatch runs and skipped
                           runs, and omits a day with minutes but no non-default head branch.

Exit codes: 0 (including "no data, nothing printed"); 2 if `gh` is missing ("install gh or pass
--from-json") or `gh api` exits non-zero (its stderr is relayed, no partial output is printed).
"""
import argparse, datetime, json, math, os, shutil, subprocess, sys

NO_GH_MSG = "install gh or pass --from-json"
# Events no pull request causes: the nightly suite and a human's manual run. `workflow_run` is
# NOT here -- the merge wake fires on the default branch because a pull request's checks finished,
# so its minute belongs to that pull request (work/ci-budget R10).
NON_PR_EVENTS = {"schedule", "workflow_dispatch"}
# Conclusions that mean "this run did not pass". `cancelled` is a human act and stays a
# completed non-failure; `null` (in progress / queued) is excluded from both sides of the ratio.
FAILURE_CONCLUSIONS = {"failure", "timed_out", "startup_failure"}


# ---------------------------------------------------------------------------
# JSON plumbing: `gh api --paginate` concatenates one JSON document per page.
# For an object-shaped endpoint (e.g. {"workflow_runs": [...]}) gh merges the
# pages into a single object itself; for an array-shaped endpoint (e.g. the
# pulls list) it prints the pages' arrays back to back, which is not one
# valid JSON document. Parse a stream of concatenated JSON documents and
# flatten them into a single list of items either way.
# ---------------------------------------------------------------------------
def _parse_json_stream(text):
    text = text.strip()
    if not text:
        return []
    decoder = json.JSONDecoder()
    items = []
    idx = 0
    n = len(text)
    while idx < n:
        while idx < n and text[idx] in " \t\r\n":
            idx += 1
        if idx >= n:
            break
        obj, end = decoder.raw_decode(text, idx)
        if isinstance(obj, list):
            items.extend(obj)
        elif isinstance(obj, dict) and "workflow_runs" in obj:
            items.extend(obj["workflow_runs"])
        else:
            items.append(obj)
        idx = end
    return items


def _gh_api(path):
    """Run `gh api --paginate <path>`, returning stdout. Exits 2 on any failure, no partial output."""
    if shutil.which("gh") is None:
        print(NO_GH_MSG, file=sys.stderr)
        sys.exit(2)
    try:
        proc = subprocess.run(["gh", "api", "--paginate", path], capture_output=True, text=True)
    except FileNotFoundError:
        print(NO_GH_MSG, file=sys.stderr)
        sys.exit(2)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        sys.exit(2)
    return proc.stdout


def _parse_iso(s):
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.datetime.fromisoformat(s)


def _api_path(metric, repo, days, workflow):
    """The `gh api` path for a metric. Runs are filtered server-side by creation date (and
    workflow); pulls have no merge-date filter, so they are fetched newest-updated first and
    `pr_cycle_series` applies `days` itself."""
    if metric in ("ci_test_failure_rate", "actions_minutes_per_pr"):
        since = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)).date().isoformat()
        if workflow:
            return f"repos/{repo}/actions/workflows/{workflow}/runs?per_page=100&created=>={since}"
        return f"repos/{repo}/actions/runs?per_page=100&created=>={since}"
    return f"repos/{repo}/pulls?state=closed&per_page=100&sort=updated&direction=desc"


# ---------------------------------------------------------------------------
# Pure functions -- fixture-testable, no network, no filesystem.
# ---------------------------------------------------------------------------
def _bucket_key(created_at, bucket):
    # Only "day" is implemented; the parameter is kept for future bucket sizes.
    return created_at[:10]


def ci_failure_series(runs, days, bucket="day"):
    """Group workflow runs into day buckets: value = failures / completed runs.

    Runs with conclusion == null (in progress / queued) are excluded from both the
    numerator and the denominator; a bucket left with zero completed runs is omitted
    entirely rather than emitted as 0/0. A failure is any conclusion in
    FAILURE_CONCLUSIONS. Only the trailing `days` buckets (measured from the most
    recent bucket present in the data, not wall-clock "now") are kept, so the
    function stays pure and reproducible against a fixed fixture. Output is
    oldest first.
    """
    buckets = {}  # date -> [failures, completed]
    for run in runs:
        created_at = run.get("created_at")
        conclusion = run.get("conclusion")
        if not created_at or conclusion is None:
            continue
        key = _bucket_key(created_at, bucket)
        failures, completed = buckets.get(key, (0, 0))
        buckets[key] = (failures + (1 if conclusion in FAILURE_CONCLUSIONS else 0), completed + 1)
    if not buckets:
        return []
    keys = sorted(buckets)
    cutoff = datetime.date.fromisoformat(keys[-1]) - datetime.timedelta(days=max(days, 1) - 1)
    return [
        buckets[key][0] / buckets[key][1]
        for key in keys
        if datetime.date.fromisoformat(key) >= cutoff
    ]


def _billed_minutes(run):
    """Minutes GitHub bills for one run: wall clock from `run_started_at` to `updated_at`,
    rounded UP to the minute, with a one-minute floor once a run has started.

    0 when either stamp is missing or the span is negative: a run that never started bills
    nothing, and clock skew between two stamps must never subtract from a bucket. The floor is
    why `skipped` runs are excluded by the caller rather than counted as zero here -- a skipped
    run never starts, so it has no `run_started_at` at all on most events, and where it does
    have one the floor would charge it a minute GitHub never billed.
    """
    started, updated = run.get("run_started_at"), run.get("updated_at")
    if not started or not updated:
        return 0
    seconds = (_parse_iso(updated) - _parse_iso(started)).total_seconds()
    if seconds < 0:
        return 0
    return max(1, math.ceil(seconds / 60.0))


def _paying_head(run, default_branch):
    """The pull request this run should be divided by, or None for the repository's own trunk.

    A run is identified by (head repository, head branch), not by the branch name alone. GitHub
    reports `head_branch` as a bare ref, so a pull request opened from a FORK's own default branch
    arrives as "main" -- the ordinary case for an outside contribution, not a contrived one. Keyed
    on the name alone it was read as this repository's trunk: its minutes counted toward the day
    and its pull request divided none of them, inflating every other pull request's average on that
    day. Since `head_branch` is chosen by whoever opens the pull request, and this series feeds
    `detect_bands.py`, which decides whether an agent is invoked with tools, that is an input an
    outsider could steer (PR-B security pass).

    Only a run on THIS repository's `default_branch` divides nothing -- the `workflow_run` merge
    wake, whose minutes a pull request caused but which is not itself one. Knowing the base
    repository is enough to rule the trunk out: a trunk run always reports `head_repository` equal
    to `repository`, so once the base is known and the head is not equal to it -- including the
    nullable case where the head repository was DELETED, which is how an outside contributor's
    fork ordinarily disappears -- the run is somebody's pull request. Requiring the head to be
    known as well would hand that contributor the same inflation back (PR-B M4 revision).

    Only when the base repository is unknown too (an older recorded response, or a hand-written
    fixture) does the name comparison apply: it cannot tell a fork from the trunk, so it keeps the
    conservative reading.
    """
    head = run.get("head_branch")
    if not head:
        return None
    head_repo = ((run.get("head_repository") or {}).get("full_name") or "").strip()
    base_repo = ((run.get("repository") or {}).get("full_name") or "").strip()
    if base_repo and head_repo != base_repo:
        return (head_repo, head)          # a fork: a pull request whatever its branch is named
    if head == default_branch:
        return None
    return (head_repo, head)


def actions_minutes_series(runs, days, default_branch="main", bucket="day"):
    """Billed Actions minutes per open pull request, one value per day, oldest first.

    Numerator: `_billed_minutes` summed over every run in the bucket that a pull request could
    have caused -- excluding `schedule` and `workflow_dispatch` (nobody's pull request), and
    excluding runs with conclusion `null` (not finished, so not yet billed a total) or `skipped`
    (GitHub bills nothing, and after R1/R3 every draft push creates two of them).

    Denominator: the distinct head branches in the bucket that are not `default_branch`, which
    is the count of pull requests that were actually paying that day. A bucket with minutes but
    no such branch -- a day of merge wakes and nothing else -- is omitted rather than divided by
    zero, and so is a bucket whose only runs were excluded above.

    Only the trailing `days` buckets, measured from the most recent surviving bucket rather than
    wall-clock "now", so the function stays pure against a fixed fixture.
    """
    minutes, branches = {}, {}
    for run in runs or []:
        created_at, conclusion = run.get("created_at"), run.get("conclusion")
        if not created_at or conclusion is None or conclusion == "skipped":
            continue
        if run.get("event") in NON_PR_EVENTS:
            continue
        key = _bucket_key(created_at, bucket)
        minutes[key] = minutes.get(key, 0) + _billed_minutes(run)
        head = _paying_head(run, default_branch)
        if head:
            branches.setdefault(key, set()).add(head)
    keys = sorted(key for key in minutes if branches.get(key))
    if not keys:
        return []
    cutoff = datetime.date.fromisoformat(keys[-1]) - datetime.timedelta(days=max(days, 1) - 1)
    return [
        minutes[key] / len(branches[key])
        for key in keys
        if datetime.date.fromisoformat(key) >= cutoff
    ]


def pr_cycle_series(prs, days):
    """Hours from created_at to merged_at for merged PRs, ordered by merged_at (oldest first).

    PRs with no merged_at (closed without merging) are skipped. Only merges within the
    trailing `days` (measured from the latest merge in the data, like ci_failure_series)
    are kept.
    """
    rows = []
    for pr in prs:
        created_at, merged_at = pr.get("created_at"), pr.get("merged_at")
        if not created_at or not merged_at:
            continue
        hours = (_parse_iso(merged_at) - _parse_iso(created_at)).total_seconds() / 3600.0
        rows.append((merged_at, hours))
    if not rows:
        return []
    rows.sort(key=lambda row: row[0])
    cutoff = _parse_iso(rows[-1][0]).date() - datetime.timedelta(days=max(days, 1) - 1)
    return [hours for merged_at, hours in rows if _parse_iso(merged_at).date() >= cutoff]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("metric", choices=["ci_test_failure_rate", "pr_cycle_time_hours",
                                       "actions_minutes_per_pr"])
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"))
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--from-json")
    ap.add_argument("--workflow", help="ci_test_failure_rate only: restrict to one workflow file or id")
    ap.add_argument("--default-branch", default="main",
                    help="actions_minutes_per_pr only: the branch that is not a pull request")
    a = ap.parse_args(argv)

    if a.metric == "actions_minutes_per_pr" and a.workflow:
        # Restricting to one workflow would divide that workflow's minutes by every pull request
        # of the day, which is not a per-pull-request cost of anything.
        print("--workflow is for ci_test_failure_rate only", file=sys.stderr)
        return 2

    if a.from_json:
        with open(a.from_json) as fh:
            data = _parse_json_stream(fh.read())
    else:
        if not a.repo:
            print("no --repo given and GITHUB_REPOSITORY is unset", file=sys.stderr)
            return 2
        data = _parse_json_stream(_gh_api(_api_path(a.metric, a.repo, a.days, a.workflow)))

    if a.metric == "ci_test_failure_rate":
        values = ci_failure_series(data, a.days)
    elif a.metric == "actions_minutes_per_pr":
        values = actions_minutes_series(data, a.days, a.default_branch)
    else:
        values = pr_cycle_series(data, a.days)

    for v in values:
        print(f"{v:.6f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
