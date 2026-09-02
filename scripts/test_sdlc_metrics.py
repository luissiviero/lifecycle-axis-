"""Tests for scripts/sdlc_metrics.py against a temp git repo.

sdlc_metrics.py resolves ROOT itself via `git rev-parse --show-toplevel`
(no cwd argument), so these tests run the script with cwd set inside the
temp repo rather than passing it a --root flag.
"""
import json, os, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SDLC_METRICS_PY = os.path.join(HERE, "sdlc_metrics.py")


def _run_git(root, args, env=None):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True, env=env)


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def _make_repo(root):
    _run_git(root, ["init", "-q"])
    _run_git(root, ["config", "user.email", "test@example.com"])
    _run_git(root, ["config", "user.name", "Test"])


def _commit_at(root, message, epoch_seconds):
    """Commit whatever is staged with both author and committer date pinned
    to epoch_seconds, so git log --since=@<ts> behaves deterministically even
    when two commits land in the same wall-clock second."""
    date = f"{epoch_seconds} +0000"
    env = dict(os.environ)
    env["GIT_AUTHOR_DATE"] = date
    env["GIT_COMMITTER_DATE"] = date
    _run_git(root, ["commit", "-q", "-m", message], env=env)


def _run_metrics(root):
    return subprocess.run(
        [sys.executable, SDLC_METRICS_PY, "--json"],
        cwd=root,
        capture_output=True,
        text=True,
    )


class SdlcMetricsScript(unittest.TestCase):
    def test_intent_to_spec_hours_and_missing_plan(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)

            base_ts = 1_700_000_000  # arbitrary fixed epoch, exactly on the hour
            intent_path = os.path.join(root, "work", "x", "intent.md")
            _write(intent_path, "---\nstatus: draft\n---\nintent\n")
            _run_git(root, ["add", "work/x/intent.md"])
            _commit_at(root, "add intent", base_ts)

            spec_path = os.path.join(root, "work", "x", "spec.md")
            _write(spec_path, "---\nstatus: draft\n---\nspec\n")
            _run_git(root, ["add", "work/x/spec.md"])
            # exactly one hour later, so intent_to_spec_hours == 1.0 even if
            # both commits happen to land in the same wall-clock second
            _commit_at(root, "add spec", base_ts + 3600)

            result = _run_metrics(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = json.loads(result.stdout)
            row = next(r for r in rows if r["work_item"] == "x")

            self.assertIsInstance(row["intent_to_spec_hours"], (int, float))
            self.assertGreaterEqual(row["intent_to_spec_hours"], 0)
            self.assertEqual(row["intent_to_spec_hours"], 1.0)

            # no plan.md was ever committed -> None, not a TypeError
            self.assertIsNone(row["spec_to_plan_hours"])

            self.assertIsInstance(row["spec_rework_after_plan"], int)
            self.assertGreaterEqual(row["spec_rework_after_plan"], 0)
            self.assertIsInstance(row["intent_rework_after_spec"], int)
            self.assertGreaterEqual(row["intent_rework_after_spec"], 0)


if __name__ == "__main__":
    unittest.main()
