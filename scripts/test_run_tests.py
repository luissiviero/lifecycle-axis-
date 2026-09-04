"""run_tests.py must keep the serial runner's contract: same exit code, same summary shape,
every module's failure output shown, and skips counted -- while running modules concurrently."""
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RUNNER = os.path.join(HERE, "run_tests.py")

OK_MODULE = textwrap.dedent(
    """
    import unittest

    class T(unittest.TestCase):
        def test_passes(self):
            self.assertTrue(True)

        @unittest.skip("on purpose")
        def test_skipped(self):
            pass

        @unittest.expectedFailure
        def test_expected_failure(self):
            self.assertTrue(False)
    """
)

BAD_MODULE = textwrap.dedent(
    """
    import unittest

    class T(unittest.TestCase):
        def test_fails(self):
            self.assertEqual(1, 2, "PLANTED_FAILURE_MARKER")
    """
)


def write(root, name, body):
    with open(os.path.join(root, name), "w", encoding="utf-8") as f:
        f.write(body)


def run(start, *extra):
    return subprocess.run(
        [sys.executable, RUNNER, "--start", start, *extra],
        capture_output=True,
        encoding="utf-8",  # the runner writes UTF-8 whatever the console code page
        errors="replace",
    )


class RunTests(unittest.TestCase):
    def test_all_green_reports_ok_with_skips_and_exit_zero(self):
        with tempfile.TemporaryDirectory() as root:
            write(root, "test_a.py", OK_MODULE)
            write(root, "test_b.py", OK_MODULE)
            r = run(root, "-j", "2")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("Ran 6 tests in", r.stdout)
            # two-word unittest labels survive aggregation instead of folding into failures=
            self.assertIn("OK (expected failures=2, skipped=2)", r.stdout)
            self.assertNotIn("failures=2,", r.stdout.replace("expected failures=2", ""))

    def test_one_failing_module_fails_the_run_and_shows_its_output(self):
        with tempfile.TemporaryDirectory() as root:
            write(root, "test_a.py", OK_MODULE)
            write(root, "test_b.py", BAD_MODULE)
            r = run(root, "-j", "2")
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("Ran 4 tests in", r.stdout)
            self.assertIn("FAILED (", r.stdout)
            self.assertIn(" failures=1", r.stdout)  # the real failure, distinct from expected failures=1
            # the failing assertion is visible without re-running anything
            self.assertIn("PLANTED_FAILURE_MARKER", r.stdout)
            self.assertIn("✘ test_b.py", r.stdout)
            self.assertIn("✔ test_a.py", r.stdout)

    def test_serial_mode_gives_the_same_verdict(self):
        with tempfile.TemporaryDirectory() as root:
            write(root, "test_a.py", OK_MODULE)
            r = run(root, "-j", "1")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("OK (expected failures=1, skipped=1)", r.stdout)

    def test_module_that_never_reaches_a_summary_is_a_failure(self):
        with tempfile.TemporaryDirectory() as root:
            # os._exit skips unittest entirely (sys.exit would be caught and reported as an
            # import error): the child exits 0 with no "Ran N tests" line, which the runner
            # must refuse to count as green.
            write(root, "test_a.py", "import os\nos._exit(0)\n")
            r = run(root, "-j", "1")
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("no summary line", r.stdout)

    def test_no_matching_modules_is_an_error(self):
        with tempfile.TemporaryDirectory() as root:
            r = run(root)
            self.assertEqual(r.returncode, 1)
            self.assertIn("no modules match", r.stderr)


if __name__ == "__main__":
    unittest.main()
