import json, os, subprocess, sys, tempfile, unittest

sys.path.insert(0, os.path.dirname(__file__))
from github_metrics import _api_path, ci_failure_series, pr_cycle_series

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, "scripts", "fixtures")
RUNS_FIXTURE = os.path.join(FIXTURES, "gh_runs.json")
PRS_FIXTURE = os.path.join(FIXTURES, "gh_prs.json")


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


if __name__ == "__main__":
    unittest.main()
