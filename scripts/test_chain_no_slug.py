"""The chain check with no slug at all (work/self-check-false-reds R1, R2, R3; spec D1, D2).

An empty `.sdlc/active` is what every delegated merge with an empty queue leaves behind
(`delegated_merge.advance`), so it is a state the check must read, not a setup mistake. With no
slug there is no `own_artifact` predicate to decide in-progress against, so the check asks the
one question that still has an answer: does the diff change anything outside `EXEMPT`? If not,
nothing needs proving and the empty pointer is a note; if so, a code change with no chain behind
it is still a failure. An explicit `--slug` that names nothing is a failure in both cases.

Composes scripts/test_check_artifact_chain.py's fixture by import, the way test_park_advance.py
composes test_delegated_merge's, so a renamed helper fails loudly here rather than passing
silently. The module is new because the plan is `kind: fix`, which locks every existing test file.

Red before the fix: `test_empty_pointer_and_exempt_diff_is_a_note` exits 1 on
`FAIL: no active work item` (check_artifact_chain.py:528). The other two cases are green today and
pin the behaviour the fix must not loosen.
"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import test_check_artifact_chain as base  # noqa: E402


def _run(root, *args):
    # Defect 3 (a separate item): the check crashes on a token with no `gh`. CI sets one, so the
    # runs here drop it, as test_check_artifact_chain.ApprovalAuthor._run_without_token does.
    env = {k: v for k, v in os.environ.items() if k not in ("GH_TOKEN", "GITHUB_TOKEN")}
    return subprocess.run([sys.executable, base.SCRIPT, *args], cwd=root,
                          capture_output=True, text=True, env=env)


def _head(root):
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True,
                          text=True, check=True).stdout.strip()


class NoSlug(unittest.TestCase):
    def _advance_shape(self, root, head_paths):
        """The shape 4eb8383 left on main: the pointer emptied in one commit (the advance), then a
        later commit touching `head_paths`. Returns the advance commit's sha, the diff base, so the
        diff holds `head_paths` only and never `.sdlc/active` itself."""
        base._write(os.path.join(root, ".sdlc", "active"), "")
        base._commit(root, "[queue-empty] Advance .sdlc/active")
        diff_base = _head(root)
        for rel in head_paths:
            base._write(os.path.join(root, rel), "x\n")
        base._commit(root, "a later commit")
        return diff_base

    # -- R1 -------------------------------------------------------------------------------------
    def test_empty_pointer_and_exempt_diff_is_a_note(self):
        with tempfile.TemporaryDirectory() as root:
            base._make_repo(root)
            diff_base = self._advance_shape(root, ["docs/note.md"])
            result = _run(root, "--base", diff_base)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(base._last_line(result.stdout), "CHAIN: PASS", result.stdout)
            self.assertIn("note: no active work item", result.stdout)
            self.assertNotIn("FAIL", result.stdout)

    # -- R2 -------------------------------------------------------------------------------------
    def test_empty_pointer_and_code_diff_still_fails(self):
        with tempfile.TemporaryDirectory() as root:
            base._make_repo(root)
            diff_base = self._advance_shape(root, ["docs/note.md", "scripts/foo.py"])
            result = _run(root, "--base", diff_base)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertEqual(base._last_line(result.stdout), "CHAIN: FAIL", result.stdout)
            self.assertIn("FAIL: no active work item", result.stdout)

    # -- R3 -------------------------------------------------------------------------------------
    def test_explicit_slug_naming_nothing_still_fails(self):
        with tempfile.TemporaryDirectory() as root:
            base._make_repo(root)
            result = _run(root, "--base", "HEAD", "--slug", "no-such-item")
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertEqual(base._last_line(result.stdout), "CHAIN: FAIL", result.stdout)
            self.assertNotIn("note: no active work item", result.stdout)


if __name__ == "__main__":
    unittest.main()
