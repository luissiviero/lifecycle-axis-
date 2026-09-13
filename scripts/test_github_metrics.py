import json, os, subprocess, sys, tempfile, unittest

sys.path.insert(0, os.path.dirname(__file__))
from github_metrics import (
    _api_path, _billed_minutes, actions_minutes_series, ci_failure_series, pr_cycle_series,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, "scripts", "fixtures")
RUNS_FIXTURE = os.path.join(FIXTURES, "gh_runs.json")
PRS_FIXTURE = os.path.join(FIXTURES, "gh_prs.json")
MINUTES_FIXTURE = os.path.join(FIXTURES, "gh_runs_minutes.json")


def _load(path):
    with open(path) as fh:
        return json.load(fh)


class CiFailureSeries(unittest.TestCase):
    def setUp(self):
        self.runs = _load(RUNS_FIXTURE)["workflow_runs"]

    def test_ordering_oldest_first(self):
        # Fixture spans 2026-08-30 (2 runs, 1 failure), 2026-08-31 (in-progress only),
        # 2026-09-01 (1 success) -- oldest bucket must come first.
        series = ci_failure_series(self.runs, 30)
        self.assertEqual(series, [0.5, 0.0])

    def test_null_conclusion_excluded_from_numerator_and_denominator(self):
        # A day with 2 runs (1 failure, 1 success): value is 1/2, not 1/3 or anything
        # counting an in-progress run in the denominator.
        series = ci_failure_series(self.runs, 30)
        self.assertAlmostEqual(series[0], 0.5)

    def test_all_in_progress_bucket_omitted_entirely(self):
        # 2026-08-31 has only a null-conclusion (in-progress) run: zero completed runs,
        # so it must not appear as a 0/0 -- or any -- entry in the output.
        series = ci_failure_series(self.runs, 30)
        self.assertEqual(len(series), 2)

    def test_single_run_day(self):
        # 2026-09-01 has exactly one completed run (a success): value is 0.0, not omitted.
        series = ci_failure_series(self.runs, 30)
        self.assertEqual(series[-1], 0.0)

    def test_empty_input(self):
        self.assertEqual(ci_failure_series([], 30), [])

    def test_days_window_trims_older_buckets(self):
        # With a 1-day window (measured back from the most recent bucket present),
        # only the 2026-09-01 bucket survives.
        series = ci_failure_series(self.runs, 1)
        self.assertEqual(series, [0.0])

    def test_timed_out_and_startup_failure_count_as_failures(self):
        # A run that timed out or never started did not pass; `cancelled` stays a
        # completed non-failure (a human act), so the day below is 3 failures of 5.
        runs = [
            {"created_at": "2026-09-02T01:00:00Z", "conclusion": "failure"},
            {"created_at": "2026-09-02T02:00:00Z", "conclusion": "timed_out"},
            {"created_at": "2026-09-02T03:00:00Z", "conclusion": "startup_failure"},
            {"created_at": "2026-09-02T04:00:00Z", "conclusion": "cancelled"},
            {"created_at": "2026-09-02T05:00:00Z", "conclusion": "success"},
        ]
        self.assertEqual(ci_failure_series(runs, 30), [0.6])


class PrCycleSeries(unittest.TestCase):
    def setUp(self):
        self.prs = _load(PRS_FIXTURE)

    def test_unmerged_pr_skipped(self):
        # Fixture has 3 PRs, only 2 merged -- the unmerged one (#102) must not appear.
        series = pr_cycle_series(self.prs, 30)
        self.assertEqual(len(series), 2)

    def test_ordering_by_merged_at_oldest_first(self):
        # PR #103 opened before #101 but merged after it -- ordering follows merged_at.
        series = pr_cycle_series(self.prs, 30)
        self.assertEqual(series, [48.0, 174.0])

    def test_hours_computed_correctly(self):
        series = pr_cycle_series(self.prs, 30)
        self.assertAlmostEqual(series[0], 48.0)
        self.assertAlmostEqual(series[1], 174.0)

    def test_empty_input(self):
        self.assertEqual(pr_cycle_series([], 30), [])

    def test_days_window_trims_older_merges(self):
        # Merges on 2026-08-22 (#101) and 2026-08-25 (#103). Measured back from the
        # latest merge: a 1-day window keeps only #103, a 4-day window keeps both.
        self.assertEqual(pr_cycle_series(self.prs, 1), [174.0])
        self.assertEqual(pr_cycle_series(self.prs, 3), [174.0])
        self.assertEqual(pr_cycle_series(self.prs, 4), [48.0, 174.0])


class ApiPaths(unittest.TestCase):
    def test_pulls_path_sorted_by_updated_desc(self):
        path = _api_path("pr_cycle_time_hours", "o/r", 30, None)
        self.assertEqual(path, "repos/o/r/pulls?state=closed&per_page=100&sort=updated&direction=desc")

    def test_runs_path_filters_by_created_and_workflow(self):
        path = _api_path("ci_test_failure_rate", "o/r", 30, "sdlc-gate.yml")
        self.assertTrue(path.startswith("repos/o/r/actions/workflows/sdlc-gate.yml/runs?per_page=100&created=>="), path)
        path = _api_path("ci_test_failure_rate", "o/r", 30, None)
        self.assertTrue(path.startswith("repos/o/r/actions/runs?per_page=100&created=>="), path)

    def test_actions_minutes_shares_the_runs_path(self):
        path = _api_path("actions_minutes_per_pr", "o/r", 30, None)
        self.assertTrue(path.startswith("repos/o/r/actions/runs?per_page=100&created=>="), path)


class EndToEndThroughDetectBands(unittest.TestCase):
    """github_metrics.py --from-json piped straight into detect_bands.py --file."""

    def _run_metrics(self, metric, fixture):
        proc = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "github_metrics.py"),
             metric, "--from-json", fixture],
            capture_output=True, text=True, cwd=ROOT,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout

    def _feed_to_detect_bands(self, series_text):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tf:
            tf.write(series_text)
            series_path = tf.name
        try:
            proc = subprocess.run(
                [sys.executable, os.path.join(ROOT, "scripts", "detect_bands.py"),
                 "--file", series_path, "--window", "2"],
                capture_output=True, text=True, cwd=ROOT,
            )
        finally:
            os.unlink(series_path)
        return proc

    def test_ci_test_failure_rate_end_to_end(self):
        # Two points and a window of two: nothing beyond the baseline to test, so no tier.
        series_text = self._run_metrics("ci_test_failure_rate", RUNS_FIXTURE)
        proc = self._feed_to_detect_bands(series_text)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertIsNone(result["tier"])
        self.assertEqual(result["tested"], 0)

    def test_pr_cycle_time_hours_end_to_end(self):
        series_text = self._run_metrics("pr_cycle_time_hours", PRS_FIXTURE)
        proc = self._feed_to_detect_bands(series_text)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertIsNone(result["tier"])
        self.assertEqual(result["tested"], 0)

    def test_actions_minutes_per_pr_end_to_end(self):
        series_text = self._run_metrics("actions_minutes_per_pr", MINUTES_FIXTURE)
        proc = self._feed_to_detect_bands(series_text)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertIsNone(result["tier"])
        self.assertEqual(result["tested"], 0)


def _run(day, started, updated, event="pull_request", conclusion="success", head_branch="claude/x"):
    """One workflow-run row. `started`/`updated` are times on `day`; either may be None."""
    return {
        "created_at": "%sT%s" % (day, started or "00:00:00Z"),
        "run_started_at": ("%sT%s" % (day, started)) if started else None,
        "updated_at": ("%sT%s" % (day, updated)) if updated else None,
        "event": event,
        "conclusion": conclusion,
        "head_branch": head_branch,
    }


class BilledMinutes(unittest.TestCase):
    """GitHub bills a started run by the wall-clock minute, rounded up, with a one-minute floor."""

    def test_a_ten_second_run_bills_the_one_minute_floor(self):
        self.assertEqual(_billed_minutes(_run("2026-09-01", "10:00:00Z", "10:00:10Z")), 1)

    def test_three_minutes_five_seconds_bills_four(self):
        self.assertEqual(_billed_minutes(_run("2026-09-01", "10:00:00Z", "10:03:05Z")), 4)

    def test_a_missing_stamp_bills_nothing(self):
        self.assertEqual(_billed_minutes(_run("2026-09-01", None, "10:03:05Z")), 0)
        self.assertEqual(_billed_minutes(_run("2026-09-01", "10:00:00Z", None)), 0)

    def test_a_negative_span_bills_nothing(self):
        # Clock skew between the two stamps must never subtract from a bucket.
        self.assertEqual(_billed_minutes(_run("2026-09-01", "10:03:05Z", "10:00:00Z")), 0)


class ActionsMinutesSeries(unittest.TestCase):
    """Billed minutes per pull request per day: the sum over runs a pull request caused,
    divided by the distinct non-default head branches that day."""

    def test_buckets_come_out_oldest_first(self):
        series = actions_minutes_series([
            _run("2026-09-02", "10:00:00Z", "10:02:00Z", head_branch="claude/b"),
            _run("2026-09-01", "10:00:00Z", "10:05:00Z", head_branch="claude/a"),
        ], days=30)
        self.assertEqual(series, [5.0, 2.0])

    def test_schedule_and_workflow_dispatch_are_excluded(self):
        # The nightly eval suite and a manual dispatch are not a pull request's cost.
        series = actions_minutes_series([
            _run("2026-09-01", "10:00:00Z", "10:02:00Z"),
            _run("2026-09-01", "11:00:00Z", "11:30:00Z", event="schedule"),
            _run("2026-09-01", "12:00:00Z", "12:30:00Z", event="workflow_dispatch"),
        ], days=30)
        self.assertEqual(series, [2.0])

    def test_a_skipped_run_is_excluded(self):
        # GitHub bills a skipped run nothing, and after R1/R3 every draft push creates two.
        series = actions_minutes_series([
            _run("2026-09-01", "10:00:00Z", "10:02:00Z"),
            _run("2026-09-01", "11:00:00Z", "11:00:03Z", conclusion="skipped"),
        ], days=30)
        self.assertEqual(series, [2.0])

    def test_a_workflow_run_wake_on_the_default_branch_counts_its_minutes(self):
        # The merge wake runs on `main` and bills a minute; the pull request caused it, so
        # its minutes land in the bucket while its branch never divides it.
        series = actions_minutes_series([
            _run("2026-09-01", "10:00:00Z", "10:02:00Z", head_branch="claude/a"),
            _run("2026-09-01", "10:03:00Z", "10:03:20Z", event="workflow_run", head_branch="main"),
        ], days=30)
        self.assertEqual(series, [3.0])

    def test_a_day_of_wakes_alone_is_omitted(self):
        # Minutes but no pull request to divide by: emit nothing rather than divide by zero.
        series = actions_minutes_series([
            _run("2026-09-01", "10:00:00Z", "10:02:00Z", event="workflow_run", head_branch="main"),
        ], days=30)
        self.assertEqual(series, [])

    def test_an_in_progress_run_omits_its_bucket(self):
        # conclusion null is queued or running: it has no billed total yet.
        series = actions_minutes_series([
            _run("2026-09-01", "10:00:00Z", "10:02:00Z", conclusion=None),
        ], days=30)
        self.assertEqual(series, [])

    def test_two_pull_requests_divide_the_day(self):
        series = actions_minutes_series([
            _run("2026-09-01", "10:00:00Z", "10:03:00Z", head_branch="claude/a"),
            _run("2026-09-01", "11:00:00Z", "11:07:00Z", head_branch="claude/b"),
        ], days=30)
        self.assertEqual(series, [5.0])

    def test_the_same_branch_twice_is_one_pull_request(self):
        series = actions_minutes_series([
            _run("2026-09-01", "10:00:00Z", "10:03:00Z", head_branch="claude/a"),
            _run("2026-09-01", "11:00:00Z", "11:07:00Z", head_branch="claude/a"),
        ], days=30)
        self.assertEqual(series, [10.0])

    def test_empty_input_is_an_empty_series(self):
        self.assertEqual(actions_minutes_series([], days=30), [])

    def test_days_trims_to_the_trailing_buckets(self):
        rows = [
            _run("2026-09-01", "10:00:00Z", "10:05:00Z", head_branch="claude/a"),
            _run("2026-09-02", "10:00:00Z", "10:02:00Z", head_branch="claude/b"),
        ]
        self.assertEqual(actions_minutes_series(rows, days=1), [2.0])

    def test_the_default_branch_is_configurable(self):
        rows = [_run("2026-09-01", "10:00:00Z", "10:02:00Z", head_branch="trunk")]
        self.assertEqual(actions_minutes_series(rows, days=30, default_branch="main"), [2.0])
        self.assertEqual(actions_minutes_series(rows, days=30, default_branch="trunk"), [])


class ActionsMinutesCli(unittest.TestCase):
    def _cli(self, *args):
        return subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "github_metrics.py")] + list(args),
            capture_output=True, text=True, cwd=ROOT,
        )

    def test_workflow_is_rejected_for_this_metric(self):
        # --workflow is for ci_test_failure_rate only, as the help text already says.
        proc = self._cli("actions_minutes_per_pr", "--from-json", MINUTES_FIXTURE,
                         "--workflow", "sdlc-gate.yml")
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertIn("--workflow", proc.stderr)

    def test_the_fixture_prints_five_then_two(self):
        proc = self._cli("actions_minutes_per_pr", "--from-json", MINUTES_FIXTURE)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.split(), ["5.000000", "2.000000"])


if __name__ == "__main__":
    unittest.main()
