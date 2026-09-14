"""Regression cases from the security pass on pull request 89 (work/advance-push).

The first module, test_delegated_merge_advance.py, was writable once: under the item's `kind: fix`
plan, `.claude/hooks/protect-tests.sh` locks a test file the moment it exists on disk, so the
review round's cases live here. The fixture is the first module's, by composition: a
`MovingRemote` instance is set up and torn down here rather than subclassed, so its six cases are
not collected a second time under this module's name.

Two Important findings, each seen red on the code before its fix:
  * the branch name reached `git fetch` as an option-capable argument, so a ref named like
    `--upload-pack=<script>` ran the script over a local or ssh origin; `--` now ends the options;
  * a merge response whose `sha` is not a string raised a TypeError out of `advance()`, past the
    `except` in `run()`, after the merge had already happened; a sha that is not a string, or not
    a sha, is now treated as absent, at both the call site and inside `advance()`.
And one nit: a detached checkout is a note, not a silent fast-forward onto the remote's default.
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
import test_delegated_merge as base  # noqa: E402
import test_delegated_merge_advance as moving  # noqa: E402


class ReviewFindings(unittest.TestCase):
    def setUp(self):
        self.fx = moving.MovingRemote("setUp")
        self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)

    def _git(self, *args):
        return self.fx._git(*args)

    def test_an_option_like_branch_name_is_a_refspec_not_a_flag(self):
        """A branch whose name begins with `--` is a refspec after `--`, never a git option. Over
        the fixture's local-path origin, `--upload-pack=<script>` without the separator ran the
        script (security pass on pull request 89, finding 1)."""
        merge_sha = self.fx._move_remote()
        marker = os.path.join(self.fx.tmp.name, "PWNED")
        script = os.path.join(self.fx.tmp.name, "pwn.sh")
        base._write(script, "#!/bin/sh\ntouch '%s'\n" % marker)
        os.chmod(script, os.stat(script).st_mode | stat.S_IXUSR)
        hostile = "refs/heads/--upload-pack=%s" % script
        self._git("update-ref", hostile, "HEAD")
        self._git("symbolic-ref", "HEAD", hostile)
        self.assertTrue(self._git("rev-parse", "--abbrev-ref", "HEAD").startswith("--upload-pack="))
        result = dm.advance(self.fx.root, self.fx.out, "merged-item", 12, self.fx.policy,
                            merge_sha=merge_sha)
        self.assertIsNone(result)
        self.assertFalse(os.path.exists(marker), "the branch name was parsed as --upload-pack")
        text = self.fx.out.stream.getvalue()
        self.assertIn("not pushed", text)
        self.assertIn("fetch of origin/--upload-pack=", text)
        self.assertEqual(self.fx._remote_tip(), merge_sha)

    def test_a_non_string_merge_sha_is_treated_as_absent(self):
        """Finding 2: a merge response with `sha: 123456789` raised `TypeError: 'int' object is
        not subscriptable` inside advance(), which run()'s except tuple does not catch, so a job
        whose merge had already happened died with a traceback. It is now the R-6 case: the
        comparison is skipped and the advance still lands."""
        merge_sha = self.fx._move_remote()
        result = dm.advance(self.fx.root, self.fx.out, "merged-item", 12, self.fx.policy,
                            merge_sha=123456789)
        self.assertEqual(result, "next-item", self.fx.out.stream.getvalue())
        tip = self.fx._remote_tip()
        self.assertEqual(self._git("rev-parse", "%s^" % tip), merge_sha)

    def test_run_drops_a_malformed_sha_before_advance(self):
        """The call site validates too: a `sha` that is not a 7-to-40 hex string reaches advance()
        as None, the same rule `--head-sha` is held to."""
        checkout = base.Checkout(self.fx.tmp.name).happy_path()
        checkout.set_fixture("PUT", "repos/%s/pulls/12/merge" % base.REPO,
                             {"merged": True, "sha": 42})
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
        self.assertIn("merge_sha", calls[0][1])
        self.assertIsNone(calls[0][1]["merge_sha"], calls[0])

    def test_a_detached_checkout_is_a_note_not_a_move(self):
        """Nit: on a detached HEAD `rev-parse --abbrev-ref HEAD` is the literal `HEAD`, `git fetch
        origin HEAD` succeeds with the remote's default, and the fast-forward moved the checkout
        silently before the push failed on the refname. Now a note, and nothing moves."""
        merge_sha = self.fx._move_remote()
        subprocess.run(["git", "-C", self.fx.root, "checkout", "-q", "--detach"], check=True,
                       capture_output=True)
        before = self._git("rev-parse", "HEAD")
        self.assertNotEqual(before, merge_sha)
        result = dm.advance(self.fx.root, self.fx.out, "merged-item", 12, self.fx.policy,
                            merge_sha=merge_sha)
        self.assertIsNone(result)
        self.assertIn("detached", self.fx.out.stream.getvalue())
        self.assertEqual(self._git("rev-parse", "HEAD"), before)
        self.assertEqual(self._git("status", "--porcelain"), "")
        self.assertEqual(self.fx._remote_tip(), merge_sha)


if __name__ == "__main__":
    unittest.main()
