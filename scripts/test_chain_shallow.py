"""The chain check on a shallow clone (work/self-check-false-reds R4, R5, R6; spec D3, D4).

`git log -G` stops at a shallow clone's graft, and the boundary commit's diff reads as the whole
file being added, so both author lookups (`^status: <s>$` at check_artifact_chain.py:833,
`^mode: delegated$` at :386) return the boundary commit as the approver -- whatever it is. On
2026-09-15 it was an agent's commit, and `main` failed on a full-clone-green chain. The fix reads
git's own shallow file and treats a boundary match as "the author check could not run", the note
branch the code already has, and never fetches: a verification step must not mutate its subject.

Composes scripts/test_check_artifact_chain.py's fixture by import. New module: `kind: fix`.

Red before the fix: `test_shallow_boundary_is_a_note_not_an_approver` fails three times on
`authored by an agent identity`. `test_full_clone_still_catches_an_agent_approval` is green today
and is the pin that stops the graft skip from becoming a way to hide a real agent approval;
`test_the_check_never_fetches` is green today and pins that nothing ever reaches the network.

The fixtures carry their own git identities (knowledge/lessons/tests-carry-their-own-environment.md).
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import test_check_artifact_chain as base  # noqa: E402

# delegated_merge.ADVANCE_IDENTITY, the author of the real boundary commit 4eb8383.
BOT = ("github-actions[bot]", "41898282+github-actions[bot]@users.noreply.github.com")
AGENT = ("claude", "noreply@anthropic.com")
NETWORK_VERBS = {"fetch", "clone", "pull", "remote", "push"}


def _env_without_token():
    return {k: v for k, v in os.environ.items() if k not in ("GH_TOKEN", "GITHUB_TOKEN")}


def _run(root, *args, env=None):
    return subprocess.run([sys.executable, base.SCRIPT, *args], cwd=root,
                          capture_output=True, text=True, env=env or _env_without_token())


def _commit_as(root, name, email, message):
    base._git(root, "add", "-A")
    base._git(root, "-c", f"user.email={email}", "-c", f"user.name={name}", "commit", "-q", "-m", message)


def _shallow_clone(origin, dest):
    """A depth-1 clone over file://, the transport that honours --depth on a local path. A git
    that cannot make one skips the case with a reason rather than passing vacuously."""
    result = subprocess.run(["git", "clone", "-q", "--depth", "1", "file://" + origin, dest],
                            capture_output=True, text=True)
    if result.returncode != 0:
        version = subprocess.run(["git", "--version"], capture_output=True, text=True).stdout.strip()
        raise unittest.SkipTest("%s cannot make a depth-1 clone over file://: %s"
                                % (version, result.stderr.strip()))
    shallow = subprocess.run(["git", "rev-parse", "--is-shallow-repository"], cwd=dest,
                             capture_output=True, text=True).stdout.strip()
    if shallow != "true":
        raise unittest.SkipTest("the clone is not shallow (--is-shallow-repository: %r)" % shallow)
    return dest


def _porcelain(root):
    return subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True,
                          text=True, check=True).stdout


class Graft(unittest.TestCase):
    def _origin_with_agent_boundary(self, tmp):
        """An approved fixture, then one unrelated commit by the bot on top, so a depth-1 clone's
        one visible commit -- its graft -- is an agent's, exactly as 4eb8383 was."""
        origin = os.path.join(tmp, "origin")
        os.makedirs(origin)
        base._make_repo(origin)
        base._write(os.path.join(origin, "README.md"), "boundary\n")
        _commit_as(origin, *BOT, "[queue-empty] an unrelated commit by the bot")
        return origin

    # -- R4 -------------------------------------------------------------------------------------
    def test_shallow_boundary_is_a_note_not_an_approver(self):
        with tempfile.TemporaryDirectory() as tmp:
            origin = self._origin_with_agent_boundary(tmp)
            clone = _shallow_clone(origin, os.path.join(tmp, "clone"))
            result = _run(clone, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(base._last_line(result.stdout), "CHAIN: PASS", result.stdout + result.stderr)
            self.assertIn("history is shallow at", result.stdout)
            self.assertNotIn("authored by an agent identity", result.stdout)

    # -- R5 -------------------------------------------------------------------------------------
    def test_full_clone_still_catches_an_agent_approval(self):
        with tempfile.TemporaryDirectory() as root:
            wd = base._make_repo(root)
            base._write(os.path.join(wd, "intent.md"), "---\nstatus: in-review\napproved-by:\n---\n# artifact\n")
            base._commit(root, "back to review")
            base._write(os.path.join(wd, "intent.md"), base._artifact("luissiviero"))
            _commit_as(root, *AGENT, "agent flips it to approved")
            result = _run(root, "--base", "HEAD")
            self.assertEqual(base._last_line(result.stdout), "CHAIN: FAIL", result.stdout)
            self.assertIn("authored by an agent identity (claude <noreply@anthropic.com>)", result.stdout)
            self.assertNotIn("history is shallow", result.stdout)

    # -- R6 -------------------------------------------------------------------------------------
    def test_the_check_never_fetches(self):
        with tempfile.TemporaryDirectory() as tmp:
            origin = self._origin_with_agent_boundary(tmp)
            clone = _shallow_clone(origin, os.path.join(tmp, "clone"))
            # A `git` first on PATH that records every argv, then hands over to the real one.
            real_git = shutil.which("git")
            bin_dir = os.path.join(tmp, "bin")
            os.makedirs(bin_dir)
            argv_log = os.path.join(tmp, "git-argv.log")
            shim = os.path.join(bin_dir, "git")
            with open(shim, "w", encoding="utf-8") as f:
                f.write('#!/bin/sh\nprintf \'%s\\n\' "$*" >> "$GIT_ARGV_LOG"\nexec "$REAL_GIT" "$@"\n')
            os.chmod(shim, 0o755)
            env = _env_without_token()
            env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")
            env["GIT_ARGV_LOG"] = argv_log
            env["REAL_GIT"] = real_git
            before = _porcelain(clone)
            _run(clone, "--slug", "demo", "--base", "HEAD", env=env)
            self.assertEqual(_porcelain(clone), before, "the check changed the working tree")
            with open(argv_log, encoding="utf-8") as f:
                calls = [line for line in f.read().splitlines() if line.strip()]
            self.assertTrue(calls, "the shim saw no git call at all; the check did not run through it")
            offenders = [c for c in calls if NETWORK_VERBS & set(c.split())]
            self.assertEqual(offenders, [], "the check reached for the network: %r" % offenders)


if __name__ == "__main__":
    unittest.main()
