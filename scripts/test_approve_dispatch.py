"""Tests for scripts/approve_dispatch.py: the role gate and the committer of the dispatch route."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import approve_dispatch  # noqa: E402

IDENTITY = "luissiviero <69210737+luissiviero@users.noreply.github.com>"


def make_repo(slug="demo"):
    root = tempfile.mkdtemp()
    subprocess.run(["git", "init", "-q", "-b", "main", root], check=True)
    subprocess.run(["git", "-C", root, "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", root, "config", "user.name", "tester"], check=True)
    os.makedirs(os.path.join(root, ".sdlc"))
    os.makedirs(os.path.join(root, "work", slug))
    shutil.copy(os.path.join(REPO, ".sdlc", "approvers.yaml"),
                os.path.join(root, ".sdlc", "approvers.yaml"))
    # Another item is active, so a test that exercises --activate produces a real change.
    with open(os.path.join(root, ".sdlc", "active"), "w") as f:
        f.write("_example\n")
    with open(os.path.join(root, "work", slug, "intent.md"), "w") as f:
        f.write("---\nstatus: in-review\n---\n# Demo\n")
    subprocess.run(["git", "-C", root, "add", "-A"], check=True)
    subprocess.run(["git", "-C", root, "commit", "-q", "-m", "init"], check=True)
    return root


def write(root, rel, text):
    path = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


class ActorCheck(unittest.TestCase):
    """R-2: the run refuses before it writes, and says why."""

    def setUp(self):
        self.root = make_repo()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def check(self, login, artifact="intent.md", **kw):
        return approve_dispatch.check_actor(login, artifact, root=self.root, **kw)

    def test_role_holder_passes(self):
        ok, reason = self.check("luissiviero")
        self.assertTrue(ok, reason)

    def test_handle_outside_the_role_is_refused(self):
        ok, reason = self.check("someone-else")
        self.assertFalse(ok)
        self.assertIn("someone-else", reason)

    def test_never_approve_handle_is_refused(self):
        ok, reason = self.check("claude[bot]")
        self.assertFalse(ok)
        self.assertIn("agent identities cannot approve", reason)

    def test_empty_actor_is_refused(self):
        ok, reason = self.check("")
        self.assertFalse(ok)
        self.assertIn("empty approver", reason)

    def test_placeholder_is_refused(self):
        ok, reason = self.check("<your-handle>")
        self.assertFalse(ok)
        self.assertIn("placeholder", reason)

    def test_cli_exits_1_and_prints_the_reason(self):
        r = subprocess.run(
            [sys.executable, os.path.join(HERE, "approve_dispatch.py"),
             "--check-actor", "someone-else", "--artifact", "intent.md", "--root", self.root],
            capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("may not approve", r.stderr)
        self.assertNotIn("ok", r.stdout)

    def test_cli_prints_ok_for_a_role_holder(self):
        r = subprocess.run(
            [sys.executable, os.path.join(HERE, "approve_dispatch.py"),
             "--check-actor", "luissiviero", "--artifact", "intent.md", "--root", self.root],
            capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "ok")


class Mode(unittest.TestCase):
    """R-8: a delegation grant lands on the default branch or nowhere."""

    def setUp(self):
        self.root = make_repo()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def check(self, **kw):
        kw.setdefault("artifact", "intent.md")
        artifact = kw.pop("artifact")
        return approve_dispatch.check_actor("luissiviero", artifact, root=self.root, **kw)

    def test_delegated_on_a_side_branch_is_refused_naming_the_ref(self):
        ok, reason = self.check(mode="delegated", ref="work/demo", default_branch="main")
        self.assertFalse(ok)
        self.assertIn("work/demo", reason)
        self.assertIn("default branch", reason)

    def test_delegated_on_the_default_branch_passes(self):
        for ref in ("main", "refs/heads/main"):
            ok, reason = self.check(mode="delegated", ref=ref, default_branch="main")
            self.assertTrue(ok, f"{ref}: {reason}")

    def test_supervised_proceeds_on_any_ref(self):
        ok, reason = self.check(mode="supervised", ref="work/demo", default_branch="main")
        self.assertTrue(ok, reason)

    def test_delegated_on_a_non_intent_artifact_is_refused(self):
        ok, reason = self.check(artifact="spec.md", mode="delegated", ref="main",
                                default_branch="main")
        self.assertFalse(ok)
        self.assertIn("intent.md", reason)

    def test_delegated_with_no_default_branch_is_refused(self):
        ok, reason = self.check(mode="delegated", ref="main")
        self.assertFalse(ok)
        self.assertIn("default branch", reason)


class Commit(unittest.TestCase):
    """R-4: the trailers, the split identity, and the staged-path allowlist."""

    def setUp(self):
        self.root = make_repo()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def git(self, *args):
        return subprocess.run(["git", "-C", self.root, *args],
                              capture_output=True, text=True).stdout.strip()

    def approve_something(self):
        write(self.root, "work/demo/intent.md", "---\nstatus: approved\n---\n# Demo\n")
        write(self.root, "work/demo/log.md", "- ts | intent.md | in-review -> approved\n")

    def run_commit(self, **kw):
        kw.setdefault("artifact", "intent.md")
        return approve_dispatch.commit("demo", "luissiviero", "12345", root=self.root,
                                       identity=IDENTITY, **kw)

    def test_message_ends_with_both_trailers(self):
        self.approve_something()
        self.assertEqual(self.run_commit(), 0)
        body = self.git("log", "-1", "--format=%B").strip()
        self.assertTrue(body.endswith("Approved-Run: 12345\nApproved-Actor: luissiviero"), body)
        self.assertTrue(body.startswith("[demo] Approve intent.md as luissiviero"), body)

    def test_note_sits_above_the_trailers(self):
        self.approve_something()
        self.assertEqual(self.run_commit(note="looks right"), 0)
        body = self.git("log", "-1", "--format=%B").strip()
        self.assertIn("looks right", body)
        self.assertTrue(body.endswith("Approved-Actor: luissiviero"), body)

    def test_author_is_the_actor_and_committer_is_the_bot(self):
        self.approve_something()
        self.assertEqual(self.run_commit(), 0)
        self.assertEqual(self.git("log", "-1", "--format=%an"), "luissiviero")
        self.assertEqual(self.git("log", "-1", "--format=%ae"),
                         "69210737+luissiviero@users.noreply.github.com")
        self.assertEqual(self.git("log", "-1", "--format=%cn"), approve_dispatch.BOT_NAME)
        self.assertEqual(self.git("log", "-1", "--format=%ce"), approve_dispatch.BOT_EMAIL)

    def test_a_stray_path_aborts_the_commit(self):
        self.approve_something()
        write(self.root, "scripts/sneaky.py", "print('hi')\n")
        before = self.git("rev-parse", "HEAD")
        self.assertEqual(self.run_commit(), 1)
        self.assertEqual(self.git("rev-parse", "HEAD"), before)

    def test_a_stray_path_is_named_in_the_refusal(self):
        self.approve_something()
        write(self.root, "scripts/sneaky.py", "print('hi')\n")
        self.assertEqual(approve_dispatch.unexpected_paths("demo", root=self.root),
                         ["scripts/sneaky.py"])

    def test_active_and_index_are_allowed(self):
        self.approve_something()
        write(self.root, ".sdlc/active", "demo\n")
        write(self.root, "work/demo/index.md", "# index\n")
        self.assertEqual(self.run_commit(), 0)
        names = self.git("show", "--name-only", "--format=", "HEAD").split()
        self.assertIn(".sdlc/active", names)
        self.assertIn("work/demo/index.md", names)

    def test_another_items_files_are_a_stray_path(self):
        self.approve_something()
        write(self.root, "work/other/intent.md", "---\nstatus: approved\n---\n")
        self.assertEqual(approve_dispatch.unexpected_paths("demo", root=self.root),
                         ["work/other/intent.md"])

    def test_nothing_to_stage_is_refused(self):
        self.assertEqual(self.run_commit(), 1)


if __name__ == "__main__":
    unittest.main()
