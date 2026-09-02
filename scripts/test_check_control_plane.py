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


class ControlPlaneRepo:
    """A throwaway git repo with a base commit on main and a head commit that
    touches .sdlc/config.env (a PROTECTED_PATHS file), plus optionally a
    non-protected file. Sets author identity for the commits."""

    def __enter__(self):
        self.root = tempfile.mkdtemp()
        _git(self.root, "init", "-q", "-b", "main")
        _git(self.root, "config", "user.email", "test@example.com")
        _git(self.root, "config", "user.name", "test")
        os.makedirs(os.path.join(self.root, ".sdlc"))
        shutil.copy(REAL_CONFIG, os.path.join(self.root, ".sdlc", "config.env"))
        with open(os.path.join(self.root, "README.md"), "w") as f:
            f.write("base\n")
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-q", "-m", "base")
        # Head commits land on a branch off main, so a three-dot diff against
        # main (the base ref) sees them.
        _git(self.root, "checkout", "-q", "-b", "head")
        return self

    def __exit__(self, *exc):
        shutil.rmtree(self.root, ignore_errors=True)

    def touch_protected(self, extra_line="agent edit\n"):
        with open(os.path.join(self.root, ".sdlc", "config.env"), "a") as f:
            f.write("# " + extra_line)
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-q", "-m", "touch protected path")

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


if __name__ == "__main__":
    unittest.main()
