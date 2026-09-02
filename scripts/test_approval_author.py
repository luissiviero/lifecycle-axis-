"""The chain check refuses an approval whose commit was authored by an agent identity."""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from test_check_artifact_chain import _make_repo, _run, _last_line  # noqa: E402


def _amend_author(root, name, email):
    subprocess.run(["git", "-C", root, "-c", f"user.name={name}", "-c", f"user.email={email}",
                    "commit", "--amend", "--no-edit", "-q", f"--author={name} <{email}>"], check=True)


class ApprovalAuthor(unittest.TestCase):
    def test_human_author_passes(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            _amend_author(root, "Luis Siviero", "luis@example.com")
            r = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(_last_line(r.stdout), "CHAIN: PASS", r.stdout)

    def test_agent_email_fails(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            _amend_author(root, "Claude", "noreply@anthropic.com")
            r = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(_last_line(r.stdout), "CHAIN: FAIL", r.stdout)
            self.assertIn("authored by an agent identity", r.stdout)

    def test_bot_handle_as_author_name_fails(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            _amend_author(root, "claude[bot]", "1234+claude[bot]@users.noreply.github.com")
            r = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(_last_line(r.stdout), "CHAIN: FAIL", r.stdout)

    def test_uncommitted_approval_is_a_note_not_a_failure(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root, approved_by="luissiviero")
            _amend_author(root, "Luis Siviero", "luis@example.com")
            # flip a file to in-review in the commit, then approve it in the working tree only
            p = os.path.join(root, "work", "demo", "spec.md")
            with open(p, encoding="utf-8") as f:
                txt = f.read()
            with open(p, "w", encoding="utf-8") as f:
                f.write(txt.replace("status: approved", "status: in-review"))
            subprocess.run(["git", "-C", root, "-c", "user.name=Luis", "-c", "user.email=luis@example.com",
                            "commit", "-qam", "unapprove"], check=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(txt)
            r = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertIn("approval not committed yet", r.stdout)


if __name__ == "__main__":
    unittest.main()
