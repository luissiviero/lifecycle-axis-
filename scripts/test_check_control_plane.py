import os, shutil, subprocess, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(HERE, "check_control_plane.sh")
REAL_CONFIG = os.path.join(ROOT, ".sdlc", "config.env")


def _run(cmd, cwd, env=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)


def _git(root, *args):
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    assert r.returncode == 0, f"git {args} failed: {r.stderr}"
    return r


CLAUDE_COAUTHOR = "touch protected path\n\nCo-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>\n"
CLAUDE_SESSION = "touch protected path\n\nClaude-Session: https://claude.ai/code/session_0123\n"


class ControlPlaneRepo:
    """A throwaway git repo with a base commit on main and a head commit that
    touches .sdlc/config.env (a PROTECTED_PATHS file), plus optionally a
    non-protected file. Sets author identity for the commits. `base_message`
    is the base commit's message (a trailer there must not count);
    `config_env` replaces the copied .sdlc/config.env."""

    def __init__(self, base_message="base", config_env=None):
        self.base_message = base_message
        self.config_env = config_env

    def __enter__(self):
        self.root = tempfile.mkdtemp()
        _git(self.root, "init", "-q", "-b", "main")
        _git(self.root, "config", "user.email", "test@example.com")
        _git(self.root, "config", "user.name", "test")
        os.makedirs(os.path.join(self.root, ".sdlc"))
        if self.config_env is None:
            shutil.copy(REAL_CONFIG, os.path.join(self.root, ".sdlc", "config.env"))
        else:
            with open(os.path.join(self.root, ".sdlc", "config.env"), "w") as f:
                f.write(self.config_env)
        with open(os.path.join(self.root, "README.md"), "w") as f:
            f.write("base\n")
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-q", "-m", self.base_message)
        # Head commits land on a branch off main, so a three-dot diff against
        # main (the base ref) sees them.
        _git(self.root, "checkout", "-q", "-b", "head")
        return self

    def __exit__(self, *exc):
        shutil.rmtree(self.root, ignore_errors=True)

    def touch_protected(self, extra_line="agent edit\n", message="touch protected path"):
        with open(os.path.join(self.root, ".sdlc", "config.env"), "a") as f:
            f.write("# " + extra_line)
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-q", "-m", message)

    def touch_unprotected(self):
        with open(os.path.join(self.root, "README.md"), "a") as f:
            f.write("more\n")
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-q", "-m", "touch readme only")

    def run_script(self, base="main", env_extra=None):
        env = dict(os.environ)
        env.pop("SDLC_PR_AUTHOR_TYPE", None)
        env.pop("SDLC_PR_HEAD_REF", None)
        env.pop("SDLC_PR_LABELS", None)
        if env_extra:
            env.update(env_extra)
        return _run(["bash", SCRIPT, base], self.root, env=env)


class CheckControlPlane(unittest.TestCase):
    def test_human_on_work_branch_touching_protected_path_passes(self):
        with ControlPlaneRepo() as repo:
            repo.touch_protected()
            r = repo.run_script(env_extra={
                "SDLC_PR_AUTHOR_TYPE": "User",
                "SDLC_PR_HEAD_REF": "work/x",
                "SDLC_PR_LABELS": "",
            })
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("human-authored", r.stdout)

    def test_agent_branch_no_label_is_blocked(self):
        with ControlPlaneRepo() as repo:
            repo.touch_protected()
            r = repo.run_script(env_extra={
                "SDLC_PR_AUTHOR_TYPE": "User",
                "SDLC_PR_HEAD_REF": "claude/foo",
                "SDLC_PR_LABELS": "",
            })
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("BLOCKED", r.stdout)

    def test_agent_branch_with_label_in_json_array_is_exempt(self):
        with ControlPlaneRepo() as repo:
            repo.touch_protected()
            r = repo.run_script(env_extra={
                "SDLC_PR_AUTHOR_TYPE": "User",
                "SDLC_PR_HEAD_REF": "claude/foo",
                "SDLC_PR_LABELS": '["other-label","control-plane-approved"]',
            })
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("EXEMPT", r.stdout)

    def test_bot_author_label_different_case_is_exempt(self):
        with ControlPlaneRepo() as repo:
            repo.touch_protected()
            r = repo.run_script(env_extra={
                "SDLC_PR_AUTHOR_TYPE": "Bot",
                "SDLC_PR_HEAD_REF": "work/x",
                "SDLC_PR_LABELS": "Control-Plane-Approved",
            })
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("EXEMPT", r.stdout)

    def test_bot_no_label_but_no_protected_paths_touched_is_clean(self):
        with ControlPlaneRepo() as repo:
            repo.touch_unprotected()
            r = repo.run_script(env_extra={
                "SDLC_PR_AUTHOR_TYPE": "Bot",
                "SDLC_PR_HEAD_REF": "work/x",
                "SDLC_PR_LABELS": "",
            })
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("clean", r.stdout)

    def test_nonexistent_base_ref_fails_with_diagnosable_message(self):
        with ControlPlaneRepo() as repo:
            repo.touch_protected()
            r = repo.run_script(base="does-not-exist-ref")
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("could not diff", (r.stdout + r.stderr))


class AgentDetection(unittest.TestCase):
    """work/control-plane-visibility spec R-6 and R-7: the kit's own PRs (kit/ and spike/ branches,
    commits with a Claude trailer under the owner's identity) are agent-authored to CI."""

    HUMAN = {"SDLC_PR_AUTHOR_TYPE": "User", "SDLC_PR_HEAD_REF": "work/x", "SDLC_PR_LABELS": ""}

    def test_kit_branch_no_label_is_blocked(self):
        with ControlPlaneRepo() as repo:
            repo.touch_protected()
            for ref in ("kit/foo", "spike/bar"):
                r = repo.run_script(env_extra={**self.HUMAN, "SDLC_PR_HEAD_REF": ref})
                self.assertEqual(r.returncode, 1, ref + r.stdout + r.stderr)
                self.assertIn("BLOCKED", r.stdout)

    def test_prefixes_come_from_config_env(self):
        with open(REAL_CONFIG, encoding="utf-8") as f:
            config = f.read().replace('AGENT_BRANCH_PREFIXES="claude/ kit/ spike/"', 'AGENT_BRANCH_PREFIXES="bot/"')
        self.assertIn('AGENT_BRANCH_PREFIXES="bot/"', config)
        with ControlPlaneRepo(config_env=config) as repo:
            repo.touch_protected()
            r = repo.run_script(env_extra={**self.HUMAN, "SDLC_PR_HEAD_REF": "bot/x"})
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("BLOCKED", r.stdout)
            # The config's list replaces the default: kit/ is a human branch under this config.
            r = repo.run_script(env_extra={**self.HUMAN, "SDLC_PR_HEAD_REF": "kit/x"})
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("human-authored", r.stdout)

    def test_claude_coauthor_trailer_on_work_branch_is_blocked(self):
        with ControlPlaneRepo() as repo:
            repo.touch_protected(message=CLAUDE_COAUTHOR)
            r = repo.run_script(env_extra=self.HUMAN)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("BLOCKED", r.stdout)

    def test_claude_session_trailer_is_blocked(self):
        with ControlPlaneRepo() as repo:
            repo.touch_protected(message=CLAUDE_SESSION)
            r = repo.run_script(env_extra=self.HUMAN)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("BLOCKED", r.stdout)

    def test_trailer_with_label_is_exempt(self):
        with ControlPlaneRepo() as repo:
            repo.touch_protected(message=CLAUDE_COAUTHOR)
            r = repo.run_script(env_extra={**self.HUMAN, "SDLC_PR_LABELS": '["control-plane-approved"]'})
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("EXEMPT", r.stdout)

    def test_trailer_only_on_base_commit_is_human(self):
        with ControlPlaneRepo(base_message=CLAUDE_COAUTHOR) as repo:
            repo.touch_protected()
            r = repo.run_script(env_extra=self.HUMAN)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("human-authored", r.stdout)


if __name__ == "__main__":
    unittest.main()
