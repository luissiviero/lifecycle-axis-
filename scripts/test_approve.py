"""Tests for scripts/approve.py: the human approval helper."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

ARTIFACT = """---
type: sdlc/{kind}
id: demo
title: Demo
description: Demo artifact.
stage: {stage}
status: in-review
approved-by:
approved-on:
timestamp: 2026-09-02T00:00:00Z
---
# Demo

## Files that change
- src/**
"""


def make_repo():
    root = tempfile.mkdtemp()
    subprocess.run(["git", "init", "-q", root], check=True)
    subprocess.run(["git", "-C", root, "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", root, "config", "user.name", "luissiviero"], check=True)
    os.makedirs(os.path.join(root, ".sdlc"))
    os.makedirs(os.path.join(root, "scripts"))
    os.makedirs(os.path.join(root, "work", "demo"))
    for f in ("config.env", "approvers.yaml"):
        shutil.copy(os.path.join(REPO, ".sdlc", f), os.path.join(root, ".sdlc", f))
    with open(os.path.join(root, ".sdlc", "active"), "w") as f:
        f.write("demo\n")
    for s in ("approve.py", "approvers.py", "log_ledger.py", "check_artifact_chain.py"):
        shutil.copy(os.path.join(HERE, s), os.path.join(root, "scripts", s))
    for kind, stage in (("intent", "plan"), ("spec", "design"), ("plan", "build")):
        with open(os.path.join(root, "work", "demo", f"{kind}.md"), "w") as f:
            f.write(ARTIFACT.format(kind=kind, stage=stage))
    subprocess.run(["git", "-C", root, "add", "-A"], check=True)
    subprocess.run(["git", "-C", root, "commit", "-q", "-m", "init"], check=True)
    return root


def run(root, *args, agent=False):
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    if agent:
        env["CLAUDECODE"] = "1"
    return subprocess.run([sys.executable, "scripts/approve.py", *args], cwd=root,
                          capture_output=True, text=True, env=env)


class Approve(unittest.TestCase):
    def setUp(self):
        self.root = make_repo()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def read(self, rel):
        with open(os.path.join(self.root, rel), encoding="utf-8") as f:
            return f.read()

    def test_approves_and_appends_ledger_then_chain_passes(self):
        r = run(self.root, "demo", "intent.md", "spec.md", "plan.md", "--as", "luissiviero", "--note", "ok")
        self.assertEqual(r.returncode, 0, r.stderr)
        for name in ("intent.md", "spec.md", "plan.md"):
            fm = self.read(f"work/demo/{name}")
            self.assertIn("status: approved", fm)
            self.assertIn("approved-by: luissiviero", fm)
            self.assertRegex(fm, r"approved-on: \d{4}-\d{2}-\d{2}")
        log = self.read("work/demo/log.md")
        self.assertEqual(log.count("-> approved | luissiviero |"), 3)
        chain = subprocess.run([sys.executable, "scripts/check_artifact_chain.py", "--slug", "demo", "--base", "HEAD"],
                               cwd=self.root, capture_output=True, text=True)
        self.assertTrue(chain.stdout.strip().endswith("CHAIN: PASS"), chain.stdout)
        self.assertIn("git add work/demo", r.stdout)

    def test_refuses_inside_agent_session(self):
        r = run(self.root, "demo", "plan.md", "--as", "luissiviero", agent=True)
        self.assertEqual(r.returncode, 3)
        self.assertIn("refused", r.stderr)
        self.assertIn("status: in-review", self.read("work/demo/plan.md"))

    def test_rejects_handle_without_role_and_bot(self):
        for handle in ("someone-else", "claude[bot]"):
            r = run(self.root, "demo", "plan.md", "--as", handle)
            self.assertEqual(r.returncode, 1, handle)
            self.assertIn("status: in-review", self.read("work/demo/plan.md"))

    def test_dry_run_writes_nothing(self):
        r = run(self.root, "demo", "plan.md", "--as", "luissiviero", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("would approve", r.stdout)
        self.assertIn("status: in-review", self.read("work/demo/plan.md"))
        self.assertFalse(os.path.exists(os.path.join(self.root, "work", "demo", "log.md")))

    def test_default_handle_from_git_config_and_activate(self):
        with open(os.path.join(self.root, ".sdlc", "active"), "w") as f:
            f.write("_example\n")
        r = run(self.root, "demo", "intent.md", "--activate")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("approved-by: luissiviero", self.read("work/demo/intent.md"))
        self.assertEqual(self.read(".sdlc/active").strip(), "demo")

    def test_already_approved_is_a_noop(self):
        run(self.root, "demo", "plan.md", "--as", "luissiviero")
        before = self.read("work/demo/log.md")
        r = run(self.root, "demo", "plan.md", "--as", "luissiviero")
        self.assertEqual(r.returncode, 0)
        self.assertIn("nothing to do", r.stdout)
        self.assertEqual(before, self.read("work/demo/log.md"))


if __name__ == "__main__":
    unittest.main()
