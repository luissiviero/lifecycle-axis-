"""Tests for .claude/hooks/stop-verify-reminder.sh (T10).

Locks in: the hook reads PLAN_REQUIRED_PATHS from .sdlc/config.env instead of
a hardcoded path list, nudges only for dirty files under configured prefixes,
and respects the .sdlc/.last-verify stamp.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hooktest import fake_repo, run_hook  # noqa: E402

HOOK = "stop-verify-reminder.sh"

REAL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _config_env(plan_required_paths: str) -> str:
    with open(os.path.join(REAL_ROOT, ".sdlc", "config.env"), encoding="utf-8") as f:
        lines = f.readlines()
    out = []
    replaced = False
    for line in lines:
        if line.startswith("PLAN_REQUIRED_PATHS="):
            out.append('PLAN_REQUIRED_PATHS="%s"\n' % plan_required_paths)
            replaced = True
        else:
            out.append(line)
    assert replaced, "PLAN_REQUIRED_PATHS= not found in .sdlc/config.env"
    return "".join(out)


class StopVerifyReminderConfiguredPaths(unittest.TestCase):
    def test_dirty_configured_path_without_stamp_nudges(self):
        cfg = _config_env("engine widgets")
        with fake_repo(config_env=cfg, **{"engine/a.py": "x = 1\n"}) as root:
            subprocess.run(["git", "-C", root, "add", "-A"], check=True)
            result = run_hook(HOOK, {"session_id": "s"}, root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")
            payload = result.stdout.strip()
            self.assertTrue(payload, "expected a nudge, got empty stdout")
            data = json.loads(payload)
            self.assertEqual(data["decision"], "block")

    def test_stamp_newer_than_dirty_file_is_silent(self):
        cfg = _config_env("engine widgets")
        with fake_repo(config_env=cfg, **{"engine/a.py": "x = 1\n"}) as root:
            subprocess.run(["git", "-C", root, "add", "-A"], check=True)
            stamp = os.path.join(root, ".sdlc", ".last-verify")
            with open(stamp, "w", encoding="utf-8") as f:
                f.write("")
            target = os.path.join(root, "engine", "a.py")
            # Stamp must be newer than the dirty file: bump its mtime 10s ahead.
            target_stat = os.stat(target)
            newer = target_stat.st_mtime + 10
            os.utime(stamp, (newer, newer))
            result = run_hook(HOOK, {"session_id": "s"}, root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            self.assertEqual(result.stderr, "")

    def test_dirty_unconfigured_path_is_silent(self):
        # Regression: src/ is not in PLAN_REQUIRED_PATHS for this fake repo, so a
        # dirty file under src/ must not trigger a nudge (the old hardcoded-list bug).
        cfg = _config_env("engine widgets")
        with fake_repo(config_env=cfg, **{"src/a.ts": "let x = 1;\n"}) as root:
            subprocess.run(["git", "-C", root, "add", "-A"], check=True)
            result = run_hook(HOOK, {"session_id": "s"}, root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            self.assertEqual(result.stderr, "")

    def test_stop_hook_active_short_circuits(self):
        cfg = _config_env("engine widgets")
        with fake_repo(config_env=cfg, **{"engine/a.py": "x = 1\n"}) as root:
            subprocess.run(["git", "-C", root, "add", "-A"], check=True)
            result = run_hook(HOOK, {"session_id": "s", "stop_hook_active": True}, root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            self.assertEqual(result.stderr, "")

    def test_empty_plan_required_paths_is_silent(self):
        cfg = _config_env("")
        with fake_repo(config_env=cfg, **{"engine/a.py": "x = 1\n"}) as root:
            subprocess.run(["git", "-C", root, "add", "-A"], check=True)
            result = run_hook(HOOK, {"session_id": "s"}, root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            self.assertEqual(result.stderr, "")

    def test_configured_prefix_missing_on_disk_is_not_an_error(self):
        # "widgets" is configured but no such directory exists in the fake repo.
        cfg = _config_env("widgets")
        with fake_repo(config_env=cfg, **{"widgets_readme.md": "not a dir\n"}) as root:
            result = run_hook(HOOK, {"session_id": "s"}, root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
