#!/usr/bin/env python3
"""GitHub-only metrics producer for the Maintain-play control-band detector (T18).

No metrics store required: everything comes straight from the GitHub API via `gh api --paginate`,
or from a saved API response for tests and offline runs. Output is one float per line, oldest
first — exactly the shape `scripts/detect_bands.py --file` accepts.

Usage:
  github_metrics.py ci_test_failure_rate  [--repo owner/name] [--days N=30] [--from-json PATH] [--workflow NAME]
  github_metrics.py pr_cycle_time_hours   [--repo owner/name] [--days N=30] [--from-json PATH]

Metrics:
  ci_test_failure_rate  -- per-day failures/completed-runs for the workflow runs endpoint.
  pr_cycle_time_hours   -- hours from PR open to merge, one value per merged PR, oldest first.

Exit codes: 0 (including "no data, nothing printed"); 2 if `gh` is missing ("install gh or pass
--from-json") or `gh api` exits non-zero (its stderr is relayed, no partial output is printed).
"""
import argparse, datetime, json, os, shutil, subprocess, sys

NO_GH_MSG = "install gh or pass --from-json"


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
    entirely rather than emitted as 0/0. Only the trailing `days` buckets (measured
    from the most recent bucket present in the data, not wall-clock "now") are kept,
    so the function stays pure and reproducible against a fixed fixture. Output is
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
        buckets[key] = (failures + (1 if conclusion == "failure" else 0), completed + 1)
    if not buckets:
        return []
    keys = sorted(buckets)
    cutoff = datetime.date.fromisoformat(keys[-1]) - datetime.timedelta(days=max(days, 1) - 1)
    return [
        buckets[key][0] / buckets[key][1]
        for key in keys
        if datetime.date.fromisoformat(key) >= cutoff
    ]


def pr_cycle_series(prs):
    """Hours from created_at to merged_at for merged PRs, ordered by merged_at (oldest first).

    PRs with no merged_at (closed without merging) are skipped.
    """
    rows = []
    for pr in prs:
        created_at, merged_at = pr.get("created_at"), pr.get("merged_at")
        if not created_at or not merged_at:
            continue
        hours = (_parse_iso(merged_at) - _parse_iso(created_at)).total_seconds() / 3600.0
        rows.append((merged_at, hours))
    rows.sort(key=lambda row: row[0])
    return [hours for _, hours in rows]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("metric", choices=["ci_test_failure_rate", "pr_cycle_time_hours"])
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"))
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--from-json")
    ap.add_argument("--workflow", help="ci_test_failure_rate only: restrict to one workflow file or id")
    a = ap.parse_args(argv)

    if a.from_json:
        with open(a.from_json) as fh:
            data = _parse_json_stream(fh.read())
    else:
        if not a.repo:
            print("no --repo given and GITHUB_REPOSITORY is unset", file=sys.stderr)
            return 2
        if a.metric == "ci_test_failure_rate":
            since = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=a.days)).date().isoformat()
            if a.workflow:
                path = f"repos/{a.repo}/actions/workflows/{a.workflow}/runs?per_page=100&created=>={since}"
            else:
                path = f"repos/{a.repo}/actions/runs?per_page=100&created=>={since}"
        else:
            path = f"repos/{a.repo}/pulls?state=closed&per_page=100"
        data = _parse_json_stream(_gh_api(path))

    if a.metric == "ci_test_failure_rate":
        values = ci_failure_series(data, a.days)
    else:
        values = pr_cycle_series(data)

    for v in values:
        print(f"{v:.6f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
