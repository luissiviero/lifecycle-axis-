import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(HERE, "check_artifact_chain.py")
REAL_CONFIG = os.path.join(ROOT, ".sdlc", "config.env")
REAL_APPROVERS = os.path.join(ROOT, ".sdlc", "approvers.yaml")


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _commit(root, message="init"):
    _git(root, "add", "-A")
    _git(root, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", message)


def _artifact(approved_by, status="approved"):
    return f"---\nstatus: {status}\napproved-by: {approved_by}\n---\n# artifact\n"


def _plan(approved_by, files="- src/**\n", status="approved"):
    return (
        f"---\nstatus: {status}\napproved-by: {approved_by}\n---\n"
        f"# plan\n\n## Files that change\n{files}\n## Release-gated\n(none)\n"
    )


def _default_log(approved_by="luissiviero"):
    return (
        f"- 2026-01-01T00:00:00Z | intent.md | in-review -> approved | {approved_by} | abc1234 |\n"
        f"- 2026-01-01T00:00:00Z | spec.md | in-review -> approved | {approved_by} | abc1234 |\n"
        f"- 2026-01-01T00:00:00Z | plan.md | in-review -> approved | {approved_by} | abc1234 |\n"
    )


def _make_repo(root, slug="demo", approved_by="luissiviero", plan_files="- src/**\n",
               log_content=None, include_log=True, branch="main"):
    """Build a minimal git repo: real .sdlc/config.env + approvers.yaml, .sdlc/active,
    work/<slug>/{intent,spec,plan}.md approved by `approved_by` (plan lists `plan_files`
    under '## Files that change'), and (unless include_log is False) a matching log.md.
    Commits everything on `branch`. Returns work/<slug>'s absolute path."""
    _git(root, "init", "-q")
    _git(root, "checkout", "-q", "-b", branch)
    os.makedirs(os.path.join(root, ".sdlc"), exist_ok=True)
    shutil.copy(REAL_CONFIG, os.path.join(root, ".sdlc", "config.env"))
    shutil.copy(REAL_APPROVERS, os.path.join(root, ".sdlc", "approvers.yaml"))
    _write(os.path.join(root, ".sdlc", "active"), slug + "\n")

    wd = os.path.join(root, "work", slug)
    _write(os.path.join(wd, "intent.md"), _artifact(approved_by))
    _write(os.path.join(wd, "spec.md"), _artifact(approved_by))
    _write(os.path.join(wd, "plan.md"), _plan(approved_by, files=plan_files))

    if include_log:
        if log_content is None:
            log_content = _default_log(approved_by)
        _write(os.path.join(wd, "log.md"), log_content)

    _commit(root)
    return wd


def _run(root, *args):
    return subprocess.run(
        ["python3", SCRIPT, *args],
        cwd=root, capture_output=True, text=True,
    )


def _last_line(text):
    lines = [l for l in text.splitlines() if l.strip()]
    return lines[-1] if lines else ""


class HappyPath(unittest.TestCase):
    def test_approved_by_luissiviero_with_matching_log_passes(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(_last_line(result.stdout), "CHAIN: PASS")


class UnknownApprover(unittest.TestCase):
    def test_bot_handle_fails_naming_agent_identities(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root, approved_by="claude[bot]")
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL")
            self.assertIn("agent identities", result.stdout)

    def test_non_role_handle_fails_naming_the_role(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root, approved_by="someone-else")
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL")
            # intent.md/spec.md require product-owner, plan.md requires tech-lead
            self.assertIn("is not a product-owner", result.stdout)
            self.assertIn("is not a tech-lead", result.stdout)


class LogEntryRequired(unittest.TestCase):
    def test_missing_entry_for_one_artifact_fails_with_renderable_line(self):
        with tempfile.TemporaryDirectory() as root:
            log_content = (
                "- 2026-01-01T00:00:00Z | intent.md | in-review -> approved | luissiviero | abc1234 |\n"
                "- 2026-01-01T00:00:00Z | plan.md | in-review -> approved | luissiviero | abc1234 |\n"
            )
            _make_repo(root, log_content=log_content)
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL")
            self.assertIn("| spec.md | in-review -> approved | luissiviero |", result.stdout)

    def test_actor_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as root:
            # approved-by is a valid approver, but the log records a different actor
            _make_repo(root, log_content=_default_log(approved_by="bob"))
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL")
            self.assertIn("no entry recording", result.stdout)

    def test_missing_log_file_fails(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root, include_log=False)
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL")
            self.assertIn("work/demo/log.md is missing", result.stdout)


class MalformedLogLine(unittest.TestCase):
    def test_malformed_line_becomes_a_note_not_a_failure(self):
        with tempfile.TemporaryDirectory() as root:
            log_content = _default_log() + "- this line is not well formed\n"
            _make_repo(root, log_content=log_content)
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(_last_line(result.stdout), "CHAIN: PASS")
            self.assertIn("note:", result.stdout)
            self.assertIn("malformed log line", result.stdout)


class NoApproversFlag(unittest.TestCase):
    def test_no_approvers_skips_approver_and_ledger_checks(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root, approved_by="claude[bot]", include_log=False)
            result = _run(root, "--slug", "demo", "--base", "HEAD", "--no-approvers")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(_last_line(result.stdout), "CHAIN: PASS")


class FilesSectionRegression(unittest.TestCase):
    """Existing behaviour: a changed file outside plan.md's '## Files that change'
    still fails the chain check."""

    def test_file_outside_plan_files_fails_against_base_branch(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)  # first commit on 'main', fully approved and logged
            _git(root, "checkout", "-q", "-b", "work/demo")
            _write(os.path.join(root, "other", "x.txt"), "hello\n")
            _commit(root, "add file outside plan")
            result = _run(root, "--slug", "demo", "--base", "main")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL")
            self.assertIn(
                "other/x.txt changed but is not listed under '## Files'", result.stdout
            )


if __name__ == "__main__":
    unittest.main()
