"""Tests for the advance after a merge when the remote has moved (work/advance-push).

The existing `Advance` fixture in test_delegated_merge.py writes its bare remote once in `setUp`
and never moves it, so every one of its cases exercises the one case production never produces:
in the workflow, the checkout is taken *before* the merge API call moves `main`, and the advance
commit was pushed onto a stale parent and rejected on every real merge. This module's fixture
moves the remote between the checkout and the advance, as the merge API does, through a second
clone that pushes a "merge" commit.

It lives in its own module because the plan is `kind: fix`, which locks every existing test file
(`.claude/hooks/protect-tests.sh`); a new file stays writable, and spec R-5 wants the existing
module unmodified as proof that nothing before the merge changed. `test_delegated_merge` is
imported as a module, not star-imported, so the loader does not collect its classes a second time.

The fixture carries its own git identity and clock (knowledge/lessons/tests-carry-their-own-environment.md).
"""
import io
import os
import stat
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import delegated_merge as dm  # noqa: E402
import delegation  # noqa: E402
import log_ledger  # noqa: E402
import test_delegated_merge as base  # noqa: E402

MERGE_SUBJECT = "Merge pull request #12 (delegated)"


class MovingRemote(unittest.TestCase):
    """Spec R-1 to R-4 and R-6: the advance fetches and fast-forwards onto the merged `main`
    before it writes, refuses when the fetched tip is not the merge commit, never resets a
    diverged checkout, and still stands down on a push rejected after the fast-forward."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = os.path.join(self.tmp.name, "checkout")
        self.other = os.path.join(self.tmp.name, "other")
        self.remote = os.path.join(self.tmp.name, "remote.git")
        subprocess.run(["git", "init", "-q", "--bare", self.remote], check=True)
        base._write(os.path.join(self.root, ".sdlc", "delegation.yaml"), base.FIXTURE_POLICY)
        base._write(os.path.join(self.root, ".sdlc", "active"), "merged-item\n")
        for slug, on in (("merged-item", "2026-09-01"), ("next-item", "2026-09-02"),
                         ("later-item", "2026-09-03")):
            base._write(os.path.join(self.root, "work", slug, "intent.md"), base.ADVANCE_INTENT % on)
            base._write(os.path.join(self.root, "work", slug, "log.md"), base.ADVANCE_LOG % slug)
        base._write(os.path.join(self.root, "work", "merged-item", "spec.md"),
                    "---\ntype: sdlc/spec\nstatus: delegated\n---\n# spec\n")
        self._git("init", "-q", "-b", "main")
        self._git("remote", "add", "origin", self.remote)
        self._git("add", "-A")
        self._commit(self.root, "fixture")
        self._git("push", "-q", "origin", "main")
        # The second clone is "GitHub": it moves the remote after the checkout above was taken.
        subprocess.run(["git", "clone", "-q", self.remote, self.other], check=True,
                       capture_output=True)
        self.policy = delegation.load(path=os.path.join(self.root, ".sdlc", "delegation.yaml"))
        self.out = dm.Run(dry_run=False, stream=io.StringIO())

    # -- helpers -------------------------------------------------------------------------------
    def _git(self, *args, cwd=None):
        return subprocess.run(["git", "-C", cwd or self.root, *args], capture_output=True,
                              text=True, check=True).stdout.strip()

    def _commit(self, cwd, message):
        self._git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.com",
                  "commit", "-q", "--allow-empty", "-m", message, cwd=cwd)

    def _move_remote(self, subject=MERGE_SUBJECT, marker="merged.txt"):
        """A commit in the second clone, pushed: the remote's main is now ahead of the checkout,
        exactly as the merge API leaves it. Returns the new tip's sha."""
        base._write(os.path.join(self.other, marker), subject + "\n")
        self._git("add", "-A", cwd=self.other)
        self._commit(self.other, subject)
        self._git("push", "-q", "origin", "main", cwd=self.other)
        return self._git("rev-parse", "HEAD", cwd=self.other)

    def _remote_tip(self):
        return subprocess.run(["git", "-C", self.remote, "rev-parse", "main"],
                              capture_output=True, text=True, check=True).stdout.strip()

    def _remote_log(self, slug):
        return subprocess.run(["git", "-C", self.remote, "show", "main:work/%s/log.md" % slug],
                              capture_output=True, text=True, check=True).stdout

    def _pointer(self):
        return dm.read_active_slug(self.root)

    # -- R-1 -----------------------------------------------------------------------------------
    def test_the_advance_lands_on_top_of_the_merge(self):
        merge_sha = self._move_remote()
        result = dm.advance(self.root, self.out, "merged-item", 12, self.policy, merge_sha=merge_sha)
        self.assertEqual(result, "next-item", self.out.stream.getvalue())
        tip = self._remote_tip()
        self.assertNotEqual(tip, merge_sha, "the advance commit never reached the remote")
        self.assertEqual(self._git("rev-parse", "%s^" % tip), merge_sha,
                         "the advance commit's parent is not the merge commit")
        self.assertIn("Advance .sdlc/active after #12 merged",
                      self._git("log", "-1", "--format=%s", tip))
        self.assertEqual(self._git("rev-parse", "HEAD"), tip)
        self.assertIn("merged as %s" % merge_sha[:7], self._remote_log("merged-item"))
        self.assertIn("ADVANCE: .sdlc/active -> next-item", self.out.stream.getvalue())

    # -- R-2 -----------------------------------------------------------------------------------
    def test_a_tip_that_is_not_the_merge_commit_is_a_note(self):
        merge_sha = self._move_remote()
        later = self._move_remote("Someone else's push right after the merge", marker="later.txt")
        self.assertNotEqual(merge_sha, later)
        before = self._git("rev-parse", "HEAD")
        result = dm.advance(self.root, self.out, "merged-item", 12, self.policy, merge_sha=merge_sha)
        self.assertIsNone(result)
        text = self.out.stream.getvalue()
        self.assertIn("not the merge commit", text)
        self.assertIn(merge_sha[:12], text)
        self.assertIn(later[:12], text)
        self.assertEqual(self._git("status", "--porcelain"), "")
        self.assertEqual(self._git("rev-parse", "HEAD"), before)
        self.assertEqual(self._pointer(), "merged-item")
        self.assertEqual(self._remote_tip(), later)

    # -- R-3 -----------------------------------------------------------------------------------
    def test_a_diverged_checkout_is_a_note_not_a_reset(self):
        merge_sha = self._move_remote()
        base._write(os.path.join(self.root, "local.txt"), "a commit the remote does not have\n")
        self._git("add", "-A")
        self._commit(self.root, "local divergence")
        local = self._git("rev-parse", "HEAD")
        result = dm.advance(self.root, self.out, "merged-item", 12, self.policy, merge_sha=merge_sha)
        self.assertIsNone(result)
        self.assertIn("could not fast-forward", self.out.stream.getvalue())
        self.assertEqual(self._git("rev-parse", "HEAD"), local)
        self.assertEqual(self._git("status", "--porcelain"), "")
        self.assertEqual(self._git("diff", "--cached", "--name-only"), "")
        self.assertEqual(self._pointer(), "merged-item")
        self.assertEqual(self._remote_tip(), merge_sha)

    # -- R-4 -----------------------------------------------------------------------------------
    def test_a_push_rejected_after_the_fast_forward_is_a_note(self):
        merge_sha = self._move_remote()
        counter = os.path.join(self.tmp.name, "attempts")
        hook = os.path.join(self.remote, "hooks", "pre-receive")
        base._write(hook, "#!/bin/sh\necho attempt >> '%s'\necho 'rejected by fixture' >&2\nexit 1\n"
                    % counter)
        os.chmod(hook, os.stat(hook).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        result = dm.advance(self.root, self.out, "merged-item", 12, self.policy, merge_sha=merge_sha)
        self.assertIsNone(result)
        self.assertIn("not pushed", self.out.stream.getvalue())
        with open(counter, encoding="utf-8") as f:
            attempts = f.read().count("attempt")
        self.assertEqual(attempts, 1, "the push was retried")
        self.assertEqual(self._remote_tip(), merge_sha)

    # -- R-6 -----------------------------------------------------------------------------------
    def test_run_passes_the_merge_sha_to_advance(self):
        """`run()` keeps the merge endpoint's response and hands its sha to `advance`. The
        end-to-end fixture's merge response carries `sha: "c" * 40`."""
        checkout = base.Checkout(self.tmp.name).happy_path()
        calls = []

        def recorder(*args, **kwargs):
            calls.append((args, kwargs))
            return None

        saved = dm.advance
        dm.advance = recorder
        self.addCleanup(setattr, dm, "advance", saved)
        self.addCleanup(setattr, dm, "API", None)
        out = io.StringIO()
        saved_stdout = sys.stdout
        sys.stdout = out
        try:
            code = dm.main(checkout.argv())
        finally:
            sys.stdout = saved_stdout
        self.assertEqual(code, 0, out.getvalue())
        self.assertEqual(len(calls), 1, calls)
        self.assertEqual(calls[0][1].get("merge_sha"), "c" * 40, calls[0])

    def test_no_merge_sha_still_fast_forwards(self):
        """A response without a sha skips the comparison but still fetches and fast-forwards, so
        the advance lands on the moved remote exactly as in R-1."""
        merge_sha = self._move_remote()
        result = dm.advance(self.root, self.out, "merged-item", 12, self.policy, merge_sha=None)
        self.assertEqual(result, "next-item", self.out.stream.getvalue())
        tip = self._remote_tip()
        self.assertEqual(self._git("rev-parse", "%s^" % tip), merge_sha)
        self.assertEqual(self._git("rev-parse", "HEAD"), tip)
        entries, malformed = log_ledger.parse(os.path.join(self.root, "work", "next-item", "log.md"))
        self.assertEqual(malformed, [])
        self.assertIn("advanced here after PR #12 merged", entries[-1].note)


if __name__ == "__main__":
    unittest.main()
