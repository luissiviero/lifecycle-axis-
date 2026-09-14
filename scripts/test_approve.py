"""Tests for scripts/approve.py: the human approval helper."""
import os
import re
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
TEMPLATE_POLICY = os.path.join(REPO, "docs", "sdlc", "templates", "delegation.yaml")

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


def run(root, *args, agent=False, env_extra=None):
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    if agent:
        env["CLAUDECODE"] = "1"
    env.update(env_extra or {})
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


def with_risk_class(text, risk_class):
    """Insert a `risk-class:` line into an ARTIFACT-shaped front matter block (spec D2's grant
    key), right after `approved-on:`, the way docs/sdlc/templates/intent.md places it."""
    return text.replace("approved-on:\n", f"approved-on:\nrisk-class: {risk_class}\n", 1)


class ApproveDelegate(unittest.TestCase):
    """scripts/approve.py --delegate (spec R-8): the human-only grant on intent.md. Only
    intent.md may carry it; it refuses a risk class the policy does not delegate, and refuses
    outright when there is no policy to check the risk class against."""

    def setUp(self):
        self.root = make_repo()
        shutil.copy(os.path.join(HERE, "delegation.py"), os.path.join(self.root, "scripts", "delegation.py"))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def read(self, rel):
        with open(os.path.join(self.root, rel), encoding="utf-8") as f:
            return f.read()

    def write_policy(self, content=None):
        if content is None:
            with open(TEMPLATE_POLICY, encoding="utf-8") as f:
                content = f.read()
        with open(os.path.join(self.root, ".sdlc", "delegation.yaml"), "w", encoding="utf-8") as f:
            f.write(content)

    def set_intent_risk_class(self, risk_class):
        path = os.path.join(self.root, "work", "demo", "intent.md")
        with open(path, encoding="utf-8") as f:
            text = f.read()
        with open(path, "w", encoding="utf-8") as f:
            f.write(with_risk_class(text, risk_class))

    def test_delegate_writes_grant_keys_and_ledger_note(self):
        self.write_policy()
        self.set_intent_risk_class("low")
        r = run(self.root, "demo", "intent.md", "--as", "luissiviero", "--delegate")
        self.assertEqual(r.returncode, 0, r.stderr)
        text = self.read("work/demo/intent.md")
        self.assertIn("status: approved", text)
        self.assertIn("approved-by: luissiviero", text)
        self.assertIn("mode: delegated", text)
        self.assertIn("delegated-by: luissiviero", text)
        self.assertRegex(text, r"delegated-on: \d{4}-\d{2}-\d{2}")
        log = self.read("work/demo/log.md")
        self.assertIn("mode: delegated", log)

    def test_delegate_refuses_risk_class_outside_policy(self):
        self.write_policy()
        self.set_intent_risk_class("medium")
        r = run(self.root, "demo", "intent.md", "--as", "luissiviero", "--delegate")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("medium", r.stderr)
        text = self.read("work/demo/intent.md")
        self.assertNotIn("mode: delegated", text)
        self.assertNotIn("status: approved", text)

    def test_delegate_refuses_with_spec_md(self):
        self.write_policy()
        r = run(self.root, "demo", "spec.md", "--as", "luissiviero", "--delegate")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("intent.md", r.stderr)
        self.assertIn("status: in-review", self.read("work/demo/spec.md"))

    def test_delegate_refuses_when_policy_missing(self):
        # No write_policy() call: .sdlc/delegation.yaml is absent.
        self.set_intent_risk_class("low")
        r = run(self.root, "demo", "intent.md", "--as", "luissiviero", "--delegate")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("delegation", r.stderr.lower())
        text = self.read("work/demo/intent.md")
        self.assertNotIn("mode: delegated", text)


LEDGER_LINE = re.compile(
    r"^- \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z (\|.*\|) [0-9a-f]{7,40} (\|.*)$")
# log.md's own front matter carries a creation timestamp, written once when the file is first made
# (approve.py's header block). Two fixtures that each create their log.md straddling a second
# boundary differ there and nowhere else, which made this comparison intermittently red in a full
# suite run while passing in isolation -- found by the plan-conformance review of pull request 51.
HEADER_TS = re.compile(r"^timestamp: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def ledger_comparable(text):
    """Blank every wall-clock and repository-local field so the rest compares byte for byte.

    Three of them: the ledger line's timestamp, the ledger line's sha (`git rev-parse --short HEAD`
    in whichever repository the call ran in, and the two fixtures are separate `git init`s), and
    log.md's front-matter creation timestamp. None is written by the code under test in a way
    --from-dispatch could change, and every other column -- artifact, from -> to, actor, note --
    is compared exactly (work/approve-by-dispatch R-3)."""
    out = []
    for line in text.split("\n"):
        line = LEDGER_LINE.sub(r"- <ts> \1 <sha> \2", line)
        out.append(HEADER_TS.sub("timestamp: <ts>", line))
    return "\n".join(out)


class ApproveFromDispatch(unittest.TestCase):
    """R-3: --from-dispatch opens the one non-shell route, and changes nothing it writes."""

    ACTIONS = {"GITHUB_ACTIONS": "true", "GITHUB_RUN_ID": "12345"}

    def setUp(self):
        self.root = make_repo()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def read(self, rel, root=None):
        with open(os.path.join(root or self.root, rel), encoding="utf-8") as f:
            return f.read()

    def test_outside_actions_exits_3(self):
        r = run(self.root, "demo", "intent.md", "--as", "luissiviero", "--from-dispatch", "12345")
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("GITHUB_RUN_ID", r.stderr)
        self.assertNotIn("status: approved", self.read("work/demo/intent.md"))

    def test_run_id_mismatch_exits_3(self):
        env = dict(self.ACTIONS, GITHUB_RUN_ID="99999")
        r = run(self.root, "demo", "intent.md", "--as", "luissiviero",
                "--from-dispatch", "12345", env_extra=env)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertNotIn("status: approved", self.read("work/demo/intent.md"))

    def test_requires_as(self):
        r = run(self.root, "demo", "intent.md", "--from-dispatch", "12345", env_extra=self.ACTIONS)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("--as", r.stderr)
        self.assertNotIn("status: approved", self.read("work/demo/intent.md"))

    def test_agent_session_still_refused_without_the_flag(self):
        r = run(self.root, "demo", "intent.md", "--as", "luissiviero", agent=True)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)

    def test_claudecode_does_not_block_a_real_dispatch(self):
        """A runner has no CLAUDECODE, but the suppression must be the flag's, not the runner's."""
        env = dict(self.ACTIONS)
        r = run(self.root, "demo", "intent.md", "--as", "luissiviero",
                "--from-dispatch", "12345", agent=True, env_extra=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("status: approved", self.read("work/demo/intent.md"))

    def test_writes_the_same_files_as_a_plain_run(self):
        other = make_repo()
        self.addCleanup(shutil.rmtree, other, ignore_errors=True)
        plain = run(other, "demo", "intent.md", "--as", "luissiviero", "--note", "n")
        self.assertEqual(plain.returncode, 0, plain.stdout + plain.stderr)
        dispatched = run(self.root, "demo", "intent.md", "--as", "luissiviero", "--note", "n",
                         "--from-dispatch", "12345", env_extra=self.ACTIONS)
        self.assertEqual(dispatched.returncode, 0, dispatched.stdout + dispatched.stderr)
        # The artifact carries only date-granular fields, so it compares byte for byte.
        self.assertEqual(self.read("work/demo/intent.md", other),
                         self.read("work/demo/intent.md"))
        self.assertEqual(ledger_comparable(self.read("work/demo/log.md", other)),
                         ledger_comparable(self.read("work/demo/log.md")))

    def test_writes_run_id_and_actor_to_github_output(self):
        out = os.path.join(self.root, "gh_output")
        env = dict(self.ACTIONS, GITHUB_OUTPUT=out)
        r = run(self.root, "demo", "intent.md", "--as", "luissiviero",
                "--from-dispatch", "12345", env_extra=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(out, encoding="utf-8") as f:
            written = f.read()
        self.assertIn("run-id=12345", written)
        self.assertIn("actor=luissiviero", written)
        self.assertIn("approved=intent.md", written)

    def test_does_not_print_the_human_commit_hint(self):
        r = run(self.root, "demo", "intent.md", "--as", "luissiviero",
                "--from-dispatch", "12345", env_extra=self.ACTIONS)
        self.assertNotIn("commit as yourself", r.stdout)


class Retire(unittest.TestCase):
    """work/retire-delegated-items R-5, R-6: --retire supersedes every present artifact as a human,
    keeps approved-by as the signature's record, and --next moves the pointer so a retired slug
    never stays in it. The fixture is make_repo's item approved by the script itself and committed,
    so the retirement has a base to be checked against."""

    ACTIONS = {"GITHUB_ACTIONS": "true", "GITHUB_RUN_ID": "12345"}

    def setUp(self):
        self.root = make_repo()
        r = run(self.root, "demo", "intent.md", "spec.md", "plan.md", "--as", "luissiviero")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.commit("approve the item")
        self.base = self.git("rev-parse", "HEAD")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def git(self, *args):
        return subprocess.run(["git", "-C", self.root, *args],
                              capture_output=True, text=True).stdout.strip()

    def commit(self, message):
        subprocess.run(["git", "-C", self.root, "add", "-A"], check=True)
        subprocess.run(["git", "-C", self.root, "commit", "-q", "-m", message], check=True)

    def read(self, rel):
        with open(os.path.join(self.root, rel), encoding="utf-8") as f:
            return f.read()

    def write(self, rel, text):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def set_front(self, name, **fields):
        """Rewrite front-matter keys on work/demo/<name> in place (a signature, a demotion)."""
        text = self.read(f"work/demo/{name}")
        for key, value in fields.items():
            text = re.sub(rf"^{key}:.*$", f"{key}: {value}", text, count=1, flags=re.M)
        self.write(f"work/demo/{name}", text)

    def retire(self, *args, **kw):
        return run(self.root, "demo", "--retire", "--as", "luissiviero", *args, **kw)

    def statuses(self):
        return {name: re.search(r"^status: (\S+)", self.read(f"work/demo/{name}"), re.M).group(1)
                for name in ("intent.md", "spec.md", "plan.md")}

    # --- R-5: the retirement ------------------------------------------------------------------

    def test_retires_every_present_artifact_and_keeps_approved_by(self):
        before = {name: self.read(f"work/demo/{name}") for name in ("intent.md", "spec.md", "plan.md")}
        r = self.retire("--note", "done")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(set(self.statuses().values()), {"superseded"})
        for name, text in before.items():
            self.assertEqual(self.read(f"work/demo/{name}"),
                             text.replace("status: approved", "status: superseded"), name)
        log = self.read("work/demo/log.md")
        self.assertEqual(log.count("| approved -> superseded | luissiviero |"), 3)
        self.assertIn("| done", log)
        self.assertIn("retired: work/demo/intent.md (approved -> superseded) by luissiviero", r.stdout)
        # The pointer named the item and no --next was given: cleared (spec D3), and the hint says so.
        self.assertEqual(self.read(".sdlc/active"), "")
        self.assertIn(".sdlc/active", r.stdout)
        # A pull request carrying exactly this retirement is green: the pointer is put back on
        # another live item first, because a moved pointer takes the check out of in-progress mode.
        self.write("work/other/intent.md", "---\nstatus: in-review\n---\n# Other\n")
        self.git("checkout", "-q", self.base)
        self.write(".sdlc/active", "other\n")
        self.write("work/other/intent.md", "---\nstatus: in-review\n---\n# Other\n")
        self.commit("point at the next item")
        base = self.git("rev-parse", "HEAD")
        self.git("checkout", "-q", "-b", "work/demo")
        for name in ("intent.md", "spec.md", "plan.md"):
            self.set_front(name, status="superseded")
        with open(os.path.join(self.root, "work", "demo", "log.md"), "a", encoding="utf-8") as f:
            f.write("".join(l + "\n" for l in log.splitlines() if "-> superseded" in l))
        self.commit("retire the item")
        env = {k: v for k, v in os.environ.items() if k not in ("GH_TOKEN", "GITHUB_TOKEN")}
        chain = subprocess.run([sys.executable, "scripts/check_artifact_chain.py", "--slug", "demo", "--base", base],
                               cwd=self.root, capture_output=True, text=True, env=env)
        self.assertTrue(chain.stdout.strip().endswith("CHAIN: PASS"), chain.stdout)

    def test_a_delegated_artifact_is_retired_from_delegated(self):
        self.set_front("spec.md", status="delegated", **{"approved-by": "claude"})
        self.commit("signed under a grant")
        r = self.retire()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("approved-by: claude", self.read("work/demo/spec.md"))
        self.assertIn("status: superseded", self.read("work/demo/spec.md"))
        self.assertIn("| spec.md | delegated -> superseded | luissiviero |", self.read("work/demo/log.md"))

    def test_refuses_an_in_review_artifact_and_writes_nothing(self):
        self.set_front("plan.md", status="in-review", **{"approved-by": ""})
        self.commit("plan back to review")
        log = self.read("work/demo/log.md")
        r = self.retire()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("work/demo/plan.md is 'in-review'", r.stderr)
        self.assertEqual(self.statuses(), {"intent.md": "approved", "spec.md": "approved", "plan.md": "in-review"})
        self.assertEqual(self.read("work/demo/log.md"), log)

    def test_a_handle_without_a_role_is_refused_before_writing(self):
        log = self.read("work/demo/log.md")
        for handle in ("someone-else", "claude[bot]"):
            r = run(self.root, "demo", "--retire", "--as", handle)
            self.assertEqual(r.returncode, 1, handle)
            self.assertIn("may not retire", r.stderr)
        self.assertEqual(set(self.statuses().values()), {"approved"})
        self.assertEqual(self.read("work/demo/log.md"), log)

    def test_already_superseded_is_a_noop(self):
        self.assertEqual(self.retire().returncode, 0)
        self.commit("retired")
        r = self.retire()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("already superseded", r.stdout)
        self.assertEqual(self.read("work/demo/log.md").count("-> superseded"), 3)
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_refuses_delegate_and_activate(self):
        r = self.retire("--activate")
        self.assertEqual(r.returncode, 1)
        self.assertIn("--next", r.stderr)
        r = self.retire("--delegate")
        self.assertEqual(r.returncode, 1)
        self.assertIn("--delegate", r.stderr)
        # No artifact and no --retire is a usage error, not an approval of nothing (plan risk 3).
        r = run(self.root, "demo", "--as", "luissiviero")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(set(self.statuses().values()), {"approved"})

    def test_agent_session_is_refused(self):
        r = self.retire(agent=True)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("refused", r.stderr)
        self.assertEqual(set(self.statuses().values()), {"approved"})

    def test_from_dispatch_writes_retired_to_github_output(self):
        out = os.path.join(self.root, "gh_output")
        r = self.retire("--from-dispatch", "12345", env_extra=dict(self.ACTIONS, GITHUB_OUTPUT=out))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(out, encoding="utf-8") as f:
            written = f.read()
        self.assertIn("retired=intent.md spec.md plan.md", written)
        self.assertIn("run-id=12345", written)
        self.assertIn("actor=luissiviero", written)
        self.assertNotIn("commit as yourself", r.stdout)

    def test_dry_run_writes_nothing(self):
        r = self.retire("--dry-run", "--next", "")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("would retire", r.stdout)
        self.assertEqual(set(self.statuses().values()), {"approved"})
        self.assertEqual(self.read(".sdlc/active"), "demo\n")
        self.assertEqual(self.git("status", "--porcelain"), "")

    # --- R-6: the pointer ---------------------------------------------------------------------

    def test_next_repoints_the_pointer(self):
        self.write("work/other/intent.md", "---\nstatus: in-review\n---\n# Other\n")
        r = self.retire("--next", "other")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.read(".sdlc/active"), "other\n")
        self.assertIn("pointer: .sdlc/active -> other", r.stdout)

    def test_blank_next_clears_a_pointer_naming_the_item(self):
        r = self.retire("--next", "")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.read(".sdlc/active"), "")
        self.assertIn("pointer: .sdlc/active cleared", r.stdout)

    def test_a_pointer_at_another_item_is_left_alone(self):
        self.write("work/other/intent.md", "---\nstatus: in-review\n---\n# Other\n")
        self.write(".sdlc/active", "other\n")
        self.commit("other item active")
        r = self.retire("--next", "")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.read(".sdlc/active"), "other\n")
        self.assertIn("left as it is", r.stdout)

    def test_next_naming_no_item_is_refused(self):
        r = self.retire("--next", "ghost")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("names no work/ghost/intent.md", r.stderr)
        self.assertEqual(set(self.statuses().values()), {"approved"})
        self.assertEqual(self.read(".sdlc/active"), "demo\n")

    def test_next_naming_a_retired_item_is_refused(self):
        self.write("work/old/intent.md", "---\nstatus: superseded\napproved-by: luissiviero\n---\n# Old\n")
        r = self.retire("--next", "old")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("is retired", r.stderr)
        self.assertEqual(set(self.statuses().values()), {"approved"})
        r = self.retire("--next", "demo")
        self.assertEqual(r.returncode, 1)
        self.assertIn("the item being retired", r.stderr)

    def test_next_with_a_traversing_slug_is_refused(self):
        for bad in ("../x", "a/b", ".."):
            r = self.retire("--next", bad)
            self.assertEqual(r.returncode, 1, bad)
            self.assertIn("is not a work-item slug", r.stderr)
        self.assertEqual(set(self.statuses().values()), {"approved"})
        self.assertEqual(self.read(".sdlc/active"), "demo\n")


if __name__ == "__main__":
    unittest.main()
