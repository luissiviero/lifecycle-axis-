"""The chain check with a token and no `gh` binary (work/chain-check-without-gh R1 to R6; spec D3, D4, D5).

`verify_dispatch_run` (check_artifact_chain.py:209) guards "cannot ask" for a missing token only; with
a token set and no `gh` on PATH -- every remote session container this repository runs in -- the
`subprocess.run(["gh", "api", ...])` at :237 raises FileNotFoundError, so the check prints a Python
stack instead of a `CHAIN:` line. The fix catches the failed exec and returns the same `(None, note)`
a missing token returns, so the caller's author rule still runs beneath it. Nothing runs before the
call to decide whether it can run: the locked suite's `DispatchAttestation._verify` stubs
`subprocess.run` at the `["gh", "api"]` boundary on machines that have no `gh`, and a lookup ahead of
the call would skip that stub (spec gotcha 1); `test_a_stubbed_subprocess_still_reaches_the_call` is
the pin.

Composes scripts/test_check_artifact_chain.py's fixture by import, the way test_chain_no_slug.py and
test_chain_shallow.py do. New module: `kind: fix` locks every existing test file.

Red before the fix: `test_a_token_with_no_gh_is_a_note_not_a_crash`,
`test_a_token_with_no_gh_still_applies_the_author_rule_to_a_forged_trailer` and
`test_the_retire_route_takes_the_same_path`. The other three are green today and pin what must not move.

The fixtures carry their own git identities, their own PATH and their own token
(knowledge/lessons/tests-carry-their-own-environment.md).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_artifact_chain as cac  # noqa: E402
import test_check_artifact_chain as base  # noqa: E402

ACTOR = "luissiviero"
AGENT_AUTHOR = "Claude <noreply@anthropic.com>"
REPO = "luissiviero/lifecycle-axis-"
NETWORK_VERBS = {"fetch", "clone", "pull", "push", "remote"}
TRAILERS = "\n\nApproved-Run: {run}\nApproved-Actor: {actor}\n"
NO_GH_NOTE = "no gh binary on PATH; the dispatch trailer was accepted on the author rule alone"


def _approve_with_trailers(root, wd, actor, author=None):
    """`status: approved` in a commit shaped as approve_dispatch.py makes one -- authored by the
    run's actor, committed by the bot, both trailers -- so the check reaches verify_dispatch_run
    (ApprovalAuthor._reapprove_with_trailers, unchanged in shape). `author` overrides the author
    line for the forged-trailer case."""
    base._write(os.path.join(wd, "intent.md"), "---\nstatus: in-review\napproved-by:\n---\n# artifact\n")
    base._commit(root, "back to review")
    base._write(os.path.join(wd, "intent.md"), base._artifact(actor))
    base._git(root, "add", "-A")
    who = author or "%s <69210737+%s@users.noreply.github.com>" % (actor, actor)
    base._git(root, "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com",
              "-c", "user.name=github-actions[bot]", "commit", "-q", "--author", who,
              "-m", "[demo] Approve intent.md" + TRAILERS.format(run="12345", actor=actor))


def _bin(tmp, name, script):
    """A directory holding one executable `name` with `script` as its body."""
    bin_dir = os.path.join(tmp, "bin-" + name)
    os.makedirs(bin_dir, exist_ok=True)
    path = os.path.join(bin_dir, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(script)
    os.chmod(path, 0o755)
    return bin_dir


def _bin_with_git_shim(tmp, argv_log):
    """A `git` first and alone on PATH that records every argv, then hands over to the real one
    (the shim of test_chain_shallow.test_the_check_never_fetches). No `gh` lives beside it."""
    return _bin(tmp, "git", '#!/bin/sh\nprintf \'%s\\n\' "$*" >> "$GIT_ARGV_LOG"\nexec "$REAL_GIT" "$@"\n')


def _env(bin_dirs, argv_log=None, token="t"):
    """The environment the check runs in: PATH is exactly `bin_dirs`, a token is set, and the
    repository is named so the check gets past its own "cannot determine the repository" guard
    (check_artifact_chain.py:234) and reaches the gh call. Nothing from os.environ but HOME."""
    env = {
        "PATH": os.pathsep.join(bin_dirs),
        "HOME": os.environ.get("HOME", "/"),
        "GITHUB_REPOSITORY": REPO,
        "REAL_GIT": shutil.which("git"),
    }
    if argv_log:
        env["GIT_ARGV_LOG"] = argv_log
    if token:
        env["GH_TOKEN"] = token
    return env


def _run_script(root, env, *args):
    return subprocess.run([sys.executable, base.SCRIPT, *args], cwd=root,
                          capture_output=True, text=True, env=env)


def _porcelain(root):
    return subprocess.run(["git", "status", "--porcelain"], cwd=root,
                          capture_output=True, text=True, check=True).stdout


class _Environ:
    """os.environ replaced wholesale for an in-process call, restored afterwards."""

    def __init__(self, env):
        self.env = env

    def __enter__(self):
        self.saved = dict(os.environ)
        os.environ.clear()
        os.environ.update(self.env)

    def __exit__(self, *exc):
        os.environ.clear()
        os.environ.update(self.saved)


class MissingBinary(unittest.TestCase):

    # -- R1 -------------------------------------------------------------------------------------
    def test_a_token_with_no_gh_is_a_note_not_a_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "repo")
            os.makedirs(root)
            wd = base._make_repo(root)
            _approve_with_trailers(root, wd, ACTOR)
            argv_log = os.path.join(tmp, "git-argv.log")
            result = _run_script(root, _env([_bin_with_git_shim(tmp, argv_log)], argv_log), "--base", "HEAD")
            self.assertNotIn("Traceback", result.stderr, result.stderr)
            self.assertEqual(base._last_line(result.stdout), "CHAIN: PASS", result.stdout + result.stderr)
            self.assertIn(NO_GH_NOTE, result.stdout)
            self.assertNotIn("no GH_TOKEN/GITHUB_TOKEN", result.stdout)

    # -- R2 -------------------------------------------------------------------------------------
    def test_a_token_with_no_gh_still_applies_the_author_rule_to_a_forged_trailer(self):
        """Security pass on pull request 51, with PATH in place of the token: a trailer nobody can
        verify must not buy anything, so an agent-authored commit carrying one still fails."""
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "repo")
            os.makedirs(root)
            wd = base._make_repo(root)
            _approve_with_trailers(root, wd, ACTOR, author=AGENT_AUTHOR)
            argv_log = os.path.join(tmp, "git-argv.log")
            result = _run_script(root, _env([_bin_with_git_shim(tmp, argv_log)], argv_log), "--base", "HEAD")
            self.assertNotIn("Traceback", result.stderr, result.stderr)
            self.assertEqual(base._last_line(result.stdout), "CHAIN: FAIL", result.stdout + result.stderr)
            self.assertIn("unverified dispatch trailer and is authored by an agent identity", result.stdout)
            self.assertIn(NO_GH_NOTE, result.stdout)

    # -- R3 -------------------------------------------------------------------------------------
    def test_the_retire_route_takes_the_same_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _Environ(_env([_bin_with_git_shim(tmp, os.path.join(tmp, "git-argv.log"))])):
                ok, detail = cac.verify_dispatch_run("12345", ACTOR, slug="demo", artifact="intent.md",
                                                     retired=True)
            self.assertIsNone(ok, detail)
            self.assertEqual(detail, NO_GH_NOTE)
            self.assertEqual(detail, cac.NO_GH_NOTE)

    # -- R4 -------------------------------------------------------------------------------------
    def test_a_present_gh_that_fails_is_still_false(self):
        """Owner's answer 2: a binary that answers non-zero is evidence, not "could not ask"."""
        with tempfile.TemporaryDirectory() as tmp:
            gh_bin = _bin(tmp, "gh", "#!/bin/sh\nprintf 'boom' >&2\nexit 1\n")
            git_bin = _bin_with_git_shim(tmp, os.path.join(tmp, "git-argv.log"))
            with _Environ(_env([gh_bin, git_bin])):
                ok, detail = cac.verify_dispatch_run("12345", ACTOR)
            self.assertIs(ok, False, detail)
            self.assertIn("could not be read", detail)
            self.assertIn("boom", detail)

    # -- R5 -------------------------------------------------------------------------------------
    def test_the_check_never_reaches_for_the_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "repo")
            os.makedirs(root)
            wd = base._make_repo(root)
            _approve_with_trailers(root, wd, ACTOR)
            argv_log = os.path.join(tmp, "git-argv.log")
            before = _porcelain(root)
            _run_script(root, _env([_bin_with_git_shim(tmp, argv_log)], argv_log), "--base", "HEAD")
            self.assertEqual(_porcelain(root), before, "the check changed the working tree")
            with open(argv_log, encoding="utf-8") as f:
                calls = [line for line in f.read().splitlines() if line.strip()]
            self.assertTrue(calls, "the shim saw no git call at all; the check did not run through it")
            offenders = [c for c in calls if NETWORK_VERBS & set(c.split())]
            self.assertEqual(offenders, [], "the check reached for the network: %r" % offenders)

    # -- R6 -------------------------------------------------------------------------------------
    def test_a_stubbed_subprocess_still_reaches_the_call(self):
        """The pin against a lookup before the call. DispatchAttestation._verify in the locked suite
        replaces subprocess.run and never has a real gh; a `shutil.which` guard ahead of the call
        would return the skipped tuple before the stub, and five green cases there would go red on
        every machine without gh (spec gotcha 1, D3)."""
        run = {"event": "workflow_dispatch", "path": cac.DISPATCH_WORKFLOW_PATH, "conclusion": "success",
               "actor": {"login": ACTOR}, "display_title": "approve: demo intent.md supervised"}
        real = cac.subprocess.run

        def fake(args, **kw):
            if args[:2] == ["gh", "api"]:
                return subprocess.CompletedProcess(args, 0, json.dumps(run), "")
            return real(args, **kw)

        with tempfile.TemporaryDirectory() as tmp:
            env = _env([_bin_with_git_shim(tmp, os.path.join(tmp, "git-argv.log"))])
            cac.subprocess.run = fake
            try:
                with _Environ(env):
                    ok, detail = cac.verify_dispatch_run("12345", ACTOR)
            finally:
                cac.subprocess.run = real
        self.assertIs(ok, True, detail)


if __name__ == "__main__":
    unittest.main()
