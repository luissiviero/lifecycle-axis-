"""Regression tests for the security-review findings on the control-plane hooks.

Finding 1: candidates were matched without canonicalisation, so `cd .sdlc && ... >> config.env`,
`work/../.sdlc/config.env` and a symlink into the control plane were allowed.
Finding 1 escalation / finding 2: SDLC_CONTROL_PLANE_UNLOCK and RELEASE_APPROVAL were read after
sourcing .sdlc/config.env, so a line planted there granted them. They are now captured from the
process environment before the config is sourced.
"""
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hooktest import REAL_ROOT, fake_repo, run_hook  # noqa: E402


def real_config() -> str:
    with open(os.path.join(REAL_ROOT, ".sdlc", "config.env"), encoding="utf-8") as f:
        return f.read()


def bash(command: str) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": command}}


def write(path: str) -> dict:
    return {"tool_name": "Write", "tool_input": {"file_path": path, "content": "x"}}


class Traversal(unittest.TestCase):
    def test_cd_then_relative_write_is_blocked(self):
        with fake_repo() as root:
            r = run_hook("protect-paths.sh", bash("cd .sdlc && echo BASH_WRITE_GUARD=0 >> config.env"), root)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn(".sdlc", r.stderr)

    def test_dotdot_in_bash_redirection_is_blocked(self):
        with fake_repo() as root:
            r = run_hook("protect-paths.sh", bash("echo x >> work/../.sdlc/config.env"), root)
            self.assertEqual(r.returncode, 2, r.stderr)

    def test_dotdot_in_write_tool_path_is_blocked(self):
        with fake_repo() as root:
            r = run_hook("protect-paths.sh", write(os.path.join(root, "work", "..", ".sdlc", "config.env")), root)
            self.assertEqual(r.returncode, 2, r.stderr)

    def test_symlink_into_control_plane_is_blocked(self):
        with fake_repo() as root:
            os.makedirs(os.path.join(root, "work"), exist_ok=True)
            os.symlink(os.path.join(root, ".sdlc"), os.path.join(root, "work", "link"))
            r = run_hook("protect-paths.sh", bash("echo x > work/link/config.env"), root)
            self.assertEqual(r.returncode, 2, r.stderr)

    def test_creating_a_symlink_to_the_control_plane_is_blocked(self):
        with fake_repo() as root:
            r = run_hook("protect-paths.sh", bash("ln -s .sdlc work/link"), root)
            self.assertEqual(r.returncode, 2, r.stderr)

    def test_reads_and_unrelated_writes_still_allowed(self):
        with fake_repo() as root:
            for cmd in ("cat .sdlc/config.env", "cd docs && echo x > notes.md", "ls > /tmp/out"):
                r = run_hook("protect-paths.sh", bash(cmd), root)
                self.assertEqual(r.returncode, 0, (cmd, r.stderr))


class SwitchesAreEnvironmentOnly(unittest.TestCase):
    def test_unlock_planted_in_config_is_ignored(self):
        cfg = real_config() + "\nSDLC_CONTROL_PLANE_UNLOCK=1\n"
        with fake_repo(config_env=cfg) as root:
            r = run_hook("protect-paths.sh", bash("cat > .sdlc/x <<'EOF'\nhi\nEOF"), root)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertNotIn("unlocked", r.stderr)

    def test_unlock_from_process_env_still_works(self):
        with fake_repo() as root:
            r = run_hook("protect-paths.sh", bash("cat > .sdlc/x <<'EOF'\nhi\nEOF"), root,
                         env={"SDLC_CONTROL_PLANE_UNLOCK": "1"})
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("unlocked", r.stderr)

    def test_release_approval_planted_in_config_is_ignored(self):
        with fake_repo() as root:
            subprocess.run(["git", "-C", root, "commit", "-q", "--allow-empty", "-m", "init"], check=True)
            sha = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
            with open(os.path.join(root, ".sdlc", "config.env"), "a", encoding="utf-8") as f:
                f.write(f"\nRELEASE_APPROVAL={sha}\n")
            r = run_hook("production-gate.sh", bash("kubectl apply -f prod.yaml"), root, env={"SDLC_UNATTENDED": "1"})
            self.assertEqual(r.returncode, 2, r.stderr)

    def test_release_approval_from_process_env_still_works(self):
        with fake_repo() as root:
            subprocess.run(["git", "-C", root, "commit", "-q", "--allow-empty", "-m", "init"], check=True)
            sha = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
            r = run_hook("production-gate.sh", bash("kubectl apply -f prod.yaml"), root,
                         env={"SDLC_UNATTENDED": "1", "RELEASE_APPROVAL": sha})
            self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
