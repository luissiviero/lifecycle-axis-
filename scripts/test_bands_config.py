import json, os, re, subprocess, sys, tempfile, unittest

sys.path.insert(0, os.path.dirname(__file__))
from bands_config import matrix, parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANDS_YAML = os.path.join(ROOT, "monitoring", "bands.yaml")
WORKFLOW = os.path.join(ROOT, ".github", "workflows", "bands.yml")
SCRIPT = os.path.join(ROOT, "scripts", "bands_config.py")

SAMPLE = """# a comment line
metrics:
  - metric: %(metric)s
    source: %(source)s
    baseline: rolling_30d
    rules: western_electric
%(window)s    tiers:
      1sigma: { action: log }
      2sigma: { action: diagnose, tools: "Read,Grep,Bash(gh run view *)" }
      3sigma: { action: propose,  routes: [pull_request, runbook:rollback] }
"""


def _sample(metric="m", source='"scripts/github_metrics.py m --days 30"', window="    window: 14\n"):
    return SAMPLE % {"metric": metric, "source": source, "window": window}


class BandsConfig(unittest.TestCase):
    def _cli(self, text):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as tf:
            tf.write(text)
            path = tf.name
        try:
            return subprocess.run([sys.executable, SCRIPT, "--file", path], capture_output=True, text=True, cwd=ROOT)
        finally:
            os.unlink(path)

    def test_real_file_yields_two_github_metrics(self):
        with open(BANDS_YAML) as fh:
            rows = matrix(parse(fh.read()))
        self.assertEqual([r["metric"] for r in rows], ["ci_test_failure_rate", "pr_cycle_time_hours"])
        self.assertEqual([r["window"] for r in rows], [14, 14])
        self.assertTrue(rows[0]["source"].endswith("--workflow sdlc-gate.yml"), rows[0]["source"])
        self.assertEqual(rows[0]["tools"], "Read,Grep,Bash(gh run view *)")
        self.assertEqual(rows[1]["tools"], "Read,Grep")
        # The CLI prints the same rows as one JSON line the workflow can fromJSON().
        proc = subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.count("\n"), 1)
        self.assertEqual(json.loads(proc.stdout), {"include": rows})

    def test_non_github_source_is_excluded(self):
        text = _sample(source='"(none — no metrics store yet; see decisions.md Q7)"')
        self.assertEqual(matrix(parse(text)), [])
        rows = matrix(parse(_sample()))
        self.assertEqual(rows, [{"metric": "m", "source": "scripts/github_metrics.py m --days 30",
                                 "tools": "Read,Grep,Bash(gh run view *)", "window": 14}])

    def test_missing_window_exits_2(self):
        proc = self._cli(_sample(window=""))
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertEqual(proc.stdout, "")
        self.assertIn("window", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)

    def test_window_below_two_exits_2(self):
        proc = self._cli(_sample(window="    window: 1\n"))
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("window", proc.stderr)
        # An unrecognised line fails loudly too, naming it.
        proc = self._cli(_sample() + "unexpected: top-level\n")
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("unexpected", proc.stderr)


class BandsWorkflow(unittest.TestCase):
    """The workflow reads its configuration from bands.yaml and never files a duplicate issue."""

    def setUp(self):
        with open(WORKFLOW) as fh:
            self.text = fh.read()

    def test_matrix_comes_from_config(self):
        self.assertIn("fromJSON(needs.config.outputs.matrix)", self.text)
        self.assertIn("--window ${{ matrix.window }}", self.text)
        self.assertIsNone(re.search(r"^\s*-?\s*metric: ci_test_failure_rate", self.text, re.M))

    def test_config_job_runs_bands_config(self):
        self.assertIn("python3 scripts/bands_config.py", self.text)
        self.assertIn("needs: config", self.text)

    def test_dedupes_open_issue(self):
        self.assertIn("gh issue list", self.text)
        self.assertGreaterEqual(self.text.count("gh issue comment"), 2)
        self.assertGreaterEqual(self.text.count("gh issue create"), 2)

    def test_uploads_series_artifact(self):
        self.assertIn("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02", self.text)

    def test_prompt_asks_only_what_tools_allow(self):
        self.assertNotIn("recent commits", self.text)


if __name__ == "__main__":
    unittest.main()
