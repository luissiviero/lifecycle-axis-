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
import log_ledger  # noqa: E402

TEMPLATE_INTENT = os.path.join(REPO, "docs", "sdlc", "templates", "intent.md")

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
            r = run(self.root, "demo", "intent.md", "--as", handle)
            self.assertEqual(r.returncode, 1, handle)
            self.assertIn("may not approve", r.stderr)
            self.assertIn("status: in-review", self.read("work/demo/intent.md"))

    def test_dry_run_writes_nothing(self):
        r = run(self.root, "demo", "intent.md", "spec.md", "--as", "luissiviero", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.count("would approve"), 2)  # spec.md counts intent.md as approved in-call
        self.assertIn("status: in-review", self.read("work/demo/intent.md"))
        self.assertIn("status: in-review", self.read("work/demo/spec.md"))
        self.assertFalse(os.path.exists(os.path.join(self.root, "work", "demo", "log.md")))

    def test_default_handle_from_git_config_and_activate(self):
        subprocess.run(["git", "-C", self.root, "config", "sdlc.approver", "luissiviero"], check=True)
        with open(os.path.join(self.root, ".sdlc", "active"), "w") as f:
            f.write("_example\n")
        r = run(self.root, "demo", "intent.md", "--activate")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("approved-by: luissiviero", self.read("work/demo/intent.md"))
        self.assertEqual(self.read(".sdlc/active").strip(), "demo")

    def test_missing_sdlc_approver_exits_1_with_hint(self):
        # The fixture's user.name is 'luissiviero' (a valid approver); success here proves the
        # display name is never consulted (spec R-7).
        r = run(self.root, "demo", "intent.md")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("--as <github-handle>", r.stderr)
        self.assertIn("sdlc.approver", r.stderr)
        self.assertIn("status: in-review", self.read("work/demo/intent.md"))
        self.assertFalse(os.path.exists(os.path.join(self.root, "work", "demo", "log.md")))

    def test_already_approved_is_a_noop(self):
        run(self.root, "demo", "intent.md", "--as", "luissiviero")
        before = self.read("work/demo/log.md")
        r = run(self.root, "demo", "intent.md", "--as", "luissiviero")
        self.assertEqual(r.returncode, 0)
        self.assertIn("nothing to do", r.stdout)
        self.assertEqual(before, self.read("work/demo/log.md"))

    def test_refuses_spec_before_intent_is_approved(self):
        r = run(self.root, "demo", "spec.md", "--as", "luissiviero")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("work/demo/spec.md needs work/demo/intent.md approved first (it is 'in-review')", r.stderr)
        self.assertIn("status: in-review", self.read("work/demo/spec.md"))
        self.assertFalse(os.path.exists(os.path.join(self.root, "work", "demo", "log.md")))

    def test_refuses_plan_before_spec_is_approved(self):
        r = run(self.root, "demo", "intent.md", "--as", "luissiviero")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = run(self.root, "demo", "plan.md", "--as", "luissiviero")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("work/demo/plan.md needs work/demo/spec.md approved first (it is 'in-review')", r.stderr)
        self.assertIn("status: in-review", self.read("work/demo/plan.md"))
        # A refused multi-artifact call writes nothing, even for the artifact that was in order.
        r = run(self.root, "demo", "plan.md", "spec.md", "--as", "luissiviero", "--note", "x")
        self.assertEqual(r.returncode, 0, r.stderr)  # given out of order, processed in chain order
        self.assertIn("status: approved", self.read("work/demo/plan.md"))
        self.assertIn("status: approved", self.read("work/demo/spec.md"))
        log = self.read("work/demo/log.md")
        self.assertLess(log.index("| spec.md |"), log.index("| plan.md |"))

    def test_template_derived_approval_yields_clean_ledger_line(self):
        """A verbatim copy of docs/sdlc/templates/intent.md approves cleanly (spec R-3)."""
        shutil.copy(TEMPLATE_INTENT, os.path.join(self.root, "work", "demo", "intent.md"))
        r = run(self.root, "demo", "intent.md", "--as", "luissiviero")
        self.assertEqual(r.returncode, 0, r.stderr)
        text = self.read("work/demo/intent.md")
        status_lines = [l for l in text.splitlines() if l.startswith("status:")]
        self.assertEqual(status_lines, ["status: approved"])
        self.assertIn("approved-by: luissiviero", text)
        entries, malformed = log_ledger.parse(os.path.join(self.root, "work", "demo", "log.md"))
        self.assertEqual(malformed, [])
        approved = log_ledger.approvals(entries, "intent.md")
        self.assertEqual(len(approved), 1)
        self.assertEqual(approved[0].from_status, "draft")
        self.assertEqual(approved[0].actor, "luissiviero")
        line = [l for l in self.read("work/demo/log.md").splitlines() if "-> approved" in l][0]
        self.assertEqual(line.count("|"), 4, line)  # five fields, no note


if __name__ == "__main__":
    unittest.main()
