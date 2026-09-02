import json, os, subprocess, sys, tempfile, unittest

sys.path.insert(0, os.path.dirname(__file__))
from github_metrics import ci_failure_series, pr_cycle_series

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


class PrCycleSeries(unittest.TestCase):
    def setUp(self):
        self.prs = _load(PRS_FIXTURE)

    def test_unmerged_pr_skipped(self):
        # Fixture has 3 PRs, only 2 merged -- the unmerged one (#102) must not appear.
        series = pr_cycle_series(self.prs)
        self.assertEqual(len(series), 2)

    def test_ordering_by_merged_at_oldest_first(self):
        # PR #103 opened before #101 but merged after it -- ordering follows merged_at.
        series = pr_cycle_series(self.prs)
        self.assertEqual(series, [48.0, 174.0])

    def test_hours_computed_correctly(self):
        series = pr_cycle_series(self.prs)
        self.assertAlmostEqual(series[0], 48.0)
        self.assertAlmostEqual(series[1], 174.0)

    def test_empty_input(self):
        self.assertEqual(pr_cycle_series([]), [])


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
        series_text = self._run_metrics("ci_test_failure_rate", RUNS_FIXTURE)
        proc = self._feed_to_detect_bands(series_text)
        self.assertIn(proc.returncode, (0, 3))
        result = json.loads(proc.stdout)
        self.assertIn("tier", result)

    def test_pr_cycle_time_hours_end_to_end(self):
        series_text = self._run_metrics("pr_cycle_time_hours", PRS_FIXTURE)
        proc = self._feed_to_detect_bands(series_text)
        self.assertIn(proc.returncode, (0, 3))
        result = json.loads(proc.stdout)
        self.assertIn("tier", result)


if __name__ == "__main__":
    unittest.main()
