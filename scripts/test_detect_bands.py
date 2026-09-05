import os, subprocess, sys, unittest
sys.path.insert(0, os.path.dirname(__file__))
from detect_bands import detect

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = [10, 11, 9, 10, 10, 11, 9, 10, 10, 10]  # mean 10, sd ≈ 0.63

class DetectBands(unittest.TestCase):
    def test_no_breach(self):
        self.assertIsNone(detect(BASE + [10, 10.5, 9.5], 10)["tier"])
    def test_three_sigma_single_point(self):
        self.assertEqual(detect(BASE + [10, 13], 10)["tier"], "3sigma")
    def test_two_sigma_two_of_three(self):
        self.assertEqual(detect(BASE + [11.5, 10, 11.5], 10)["tier"], "2sigma")
    def test_one_sigma_four_of_five(self):
        self.assertEqual(detect(BASE + [10.8, 10.8, 10, 10.8, 10.8], 10)["tier"], "1sigma")
    def test_needs_points_beyond_window(self):
        self.assertIsNone(detect(BASE, 10)["tier"])

    # A healthy series has zero variance; the first bad point must still breach (spec R-1).
    def test_flat_baseline_then_spike(self):
        r = detect([0] * 30 + [1], 14)
        self.assertEqual(r["tier"], "3sigma")
        self.assertEqual(r["index"], 30)
        self.assertEqual(r["sd"], 0)
        self.assertEqual(detect([0] * 30 + [1], 30)["tier"], "3sigma")  # default window too
    def test_flat_series_is_not_a_breach(self):
        self.assertIsNone(detect([0] * 31, 14)["tier"])
    # Every point after the first window is tested; the highest tier wins (R-2).
    def test_earlier_three_sigma_in_tail_is_reported(self):
        r = detect(BASE + [13, 10, 10, 10], 10)
        self.assertEqual(r["tier"], "3sigma")
        self.assertEqual(r["index"], 10)
    def test_baseline_trails_the_tested_run(self):
        r = detect([0] * 14 + [5] * 15, 14)
        self.assertEqual(r["tier"], "3sigma")
        self.assertEqual(r["index"], 14)
        self.assertEqual(r["tested"], 15)
    def test_downward_breach(self):
        r = detect(BASE + [10, 7], 10)
        self.assertEqual(r["tier"], "3sigma")
        self.assertEqual(r["side"], -1)
    # Fourth Western Electric rule (R-4).
    def test_drift_eight_on_one_side(self):
        r = detect(BASE + [10.2] * 8, 10)
        self.assertEqual(r["tier"], "drift")
        self.assertEqual(r["acts_as"], "1sigma")
        self.assertEqual(r["side"], 1)
    def test_seven_on_one_side_is_not_drift(self):
        self.assertIsNone(detect(BASE + [10.2] * 7, 10)["tier"])


class DetectBandsCli(unittest.TestCase):
    """Bad input is a message and exit 2, never a traceback (R-5)."""

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "detect_bands.py"), *args],
            capture_output=True, text=True, cwd=ROOT,
        )

    def _assert_rejected(self, proc):
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertEqual(proc.stdout, "")
        self.assertTrue(proc.stderr.startswith("detect_bands:"), proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)

    def test_window_below_two_exits_2(self):
        self._assert_rejected(self._run("--series", "1,2,3", "--window", "1"))
        self._assert_rejected(self._run("--series", "1,2,3", "--window", "0"))

    def test_nan_exits_2(self):
        self._assert_rejected(self._run("--series", "1,nan,3", "--window", "2"))
        self._assert_rejected(self._run("--series", "1,inf,3", "--window", "2"))

    def test_non_numeric_exits_2(self):
        self._assert_rejected(self._run("--series", "1,x,3", "--window", "2"))

    def test_breach_exits_3(self):
        proc = self._run("--series", ",".join(["0"] * 30 + ["1"]), "--window", "14")
        self.assertEqual(proc.returncode, 3, proc.stderr)
        self.assertIn('"tier": "3sigma"', proc.stdout)


if __name__ == "__main__": unittest.main()
