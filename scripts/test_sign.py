"""Tests for scripts/sign.py: the agent's own signing script under a delegated-mode grant
(work/delegated-mode R-7, D3).

sign.py is approve.py's mirror, run the other way round: approve.py refuses inside an agent
session and only a human may run it; sign.py refuses OUTSIDE an agent session (exit 3, no
CLAUDECODE) and is the only script that may set `status: delegated` on the honest path. Every
other refusal (policy off, no grant, wrong handle, wrong artifact, chain out of order, a missing
or insufficient revision record) exits 1 and writes nothing, mirroring approve.py's
validate-everything-then-write structure (spec D3).

Fixture: a temp git repo with the real .sdlc/config.env and .sdlc/approvers.yaml (luissiviero
holds every role; claude/claude[bot]/github-actions[bot] sit in never-approve, exactly as this
repo's own file has them), .sdlc/delegation.yaml built from docs/sdlc/templates/delegation.yaml
(the exact policy content adopters copy), and work/demo/{intent,spec,plan,log}.md: intent.md
approved by luissiviero with `mode: delegated` and `risk-class: low`, spec.md and plan.md
`in-review`. Tests that want a different starting shape (policy off, intent not granted, an
already-signed spec.md, ...) pass the matching make_repo() keyword.
"""
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

TEMPLATE_POLICY_PATH = os.path.join(REPO, "docs", "sdlc", "templates", "delegation.yaml")
with open(TEMPLATE_POLICY_PATH, encoding="utf-8") as _f:
    TEMPLATE_POLICY_TEXT = _f.read()

SCRIPTS_TO_COPY = (
    "sign.py", "approve.py", "approvers.py", "log_ledger.py",
    "check_artifact_chain.py", "delegation.py",
)

REVISION_TWO_REVIEWERS_REVISE = """\
---
type: sdlc/revision
id: demo-revision-1
title: Revise the spec
description: Fix X.
artifact: spec.md
trigger: "blocking error found in review; evidence: scripts/run_tests.py:1 fake failure"
timestamp: 2026-09-05T02:00:00Z
---
## Proposal
Change X because Y.

## Reviewer: security (gpt-5)
Findings noted; the trigger is real and this is the smallest fix.
verdict: revise

## Reviewer: architecture (gemini)
Agrees; nothing else in the plan goes stale.
verdict: revise
"""

REVISION_ONE_REVIEWER = """\
---
type: sdlc/revision
id: demo-revision-1
title: Revise the spec
description: Fix X.
artifact: spec.md
trigger: "blocking error found in review"
timestamp: 2026-09-05T02:00:00Z
---
## Proposal
Change X because Y.

## Reviewer: security (gpt-5)
Findings noted.
verdict: revise
"""

REVISION_ONE_KEEP = """\
---
type: sdlc/revision
id: demo-revision-1
title: Revise the spec
description: Fix X.
artifact: spec.md
trigger: "blocking error found in review"
timestamp: 2026-09-05T02:00:00Z
---
## Proposal
Change X because Y.

## Reviewer: security (gpt-5)
Findings noted.
verdict: revise

## Reviewer: architecture (gemini)
Disagrees; the plan is fine as is.
verdict: keep
"""


def _intent(status="approved", approved_by="luissiviero", mode="delegated", risk_class="low"):
    delegated_by = approved_by if mode == "delegated" else ""
    delegated_on = "2026-09-01" if mode == "delegated" else ""
    return (
        "---\n"
        f"status: {status}\n"
        f"approved-by: {approved_by}\n"
        "approved-on: 2026-09-01\n"
        f"risk-class: {risk_class}\n"
        f"mode: {mode}\n"
        f"delegated-by: {delegated_by}\n"
        f"delegated-on: {delegated_on}\n"
        "---\n# Intent\n"
    )


def _artifact(status="in-review", approved_by=""):
    approved_on = "2026-09-01" if approved_by else ""
    return (
        "---\n"
        f"status: {status}\n"
        f"approved-by: {approved_by}\n"
        f"approved-on: {approved_on}\n"
        "---\n# Artifact\n"
    )


def _plan(status="in-review", approved_by=""):
    approved_on = "2026-09-01" if approved_by else ""
    return (
        "---\n"
        f"status: {status}\n"
        f"approved-by: {approved_by}\n"
        f"approved-on: {approved_on}\n"
        "---\n# Plan\n\n## Files that change\n- scripts/**\n\n## Release-gated\n(none)\n"
    )


def _log(intent_by="luissiviero", extra=""):
    return (
        "---\ntype: sdlc/log\nid: demo-log\ntitle: Gate ledger for demo\n"
        "timestamp: 2026-09-01T00:00:00Z\n---\n# Log: demo\n\n"
        "Format: `- <RFC3339> | <artifact> | <from> -> <to> | <actor> | <sha> | <note>` "
        "(append-only; parsed by scripts/log_ledger.py).\n\n"
        f"- 2026-09-01T00:00:00Z | intent.md | in-review -> approved | {intent_by} | abc1234 |\n"
        f"- 2026-09-01T00:00:00Z | intent.md | approved -> approved | {intent_by} | abc1234 | mode: delegated\n"
        f"{extra}"
    )


def make_repo(root, intent_status="approved", intent_mode="delegated", risk_class="low",
              spec_status="in-review", spec_by="", plan_status="in-review", plan_by="",
              write_policy=True, policy_content=None, extra_log=""):
    """Build work/demo under `root`: a granted intent.md (unless overridden) plus spec.md and
    plan.md at the given status/signer, a matching log.md, the real config/approvers files, the
    delegation policy (template content by default), and every scripts/ module sign.py needs."""
    subprocess.run(["git", "init", "-q", root], check=True)
    subprocess.run(["git", "-C", root, "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", root, "config", "user.name", "luissiviero"], check=True)
    os.makedirs(os.path.join(root, ".sdlc"), exist_ok=True)
    os.makedirs(os.path.join(root, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(root, "work", "demo"), exist_ok=True)

    for f in ("config.env", "approvers.yaml"):
        shutil.copy(os.path.join(REPO, ".sdlc", f), os.path.join(root, ".sdlc", f))
    with open(os.path.join(root, ".sdlc", "active"), "w", encoding="utf-8") as f:
        f.write("demo\n")
    if write_policy:
        with open(os.path.join(root, ".sdlc", "delegation.yaml"), "w", encoding="utf-8") as f:
            f.write(policy_content if policy_content is not None else TEMPLATE_POLICY_TEXT)

    for s in SCRIPTS_TO_COPY:
        shutil.copy(os.path.join(HERE, s), os.path.join(root, "scripts", s))

    with open(os.path.join(root, "work", "demo", "intent.md"), "w", encoding="utf-8") as f:
        f.write(_intent(status=intent_status, mode=intent_mode, risk_class=risk_class))
    with open(os.path.join(root, "work", "demo", "spec.md"), "w", encoding="utf-8") as f:
        f.write(_artifact(status=spec_status, approved_by=spec_by))
    with open(os.path.join(root, "work", "demo", "plan.md"), "w", encoding="utf-8") as f:
        f.write(_plan(status=plan_status, approved_by=plan_by))
    with open(os.path.join(root, "work", "demo", "log.md"), "w", encoding="utf-8") as f:
        f.write(_log(extra=extra_log))

    subprocess.run(["git", "-C", root, "add", "-A"], check=True)
    subprocess.run(["git", "-C", root, "commit", "-q", "-m", "init"], check=True)


def run(root, *args, claudecode=True, handle=None):
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDECODE", "SDLC_AGENT_HANDLE")}
    if claudecode:
        env["CLAUDECODE"] = "1"
    if handle is not None:
        env["SDLC_AGENT_HANDLE"] = handle
    return subprocess.run([sys.executable, "scripts/sign.py", *args], cwd=root,
                          capture_output=True, text=True, env=env)


def read(root, rel):
    with open(os.path.join(root, rel), encoding="utf-8") as f:
        return f.read()


def _spec_sign_line(status, by):
    """The ledger line a prior human approval or agent signature of spec.md would already have
    left behind, so a fixture that starts spec.md at `status` is internally consistent."""
    return f"- 2026-09-02T00:00:00Z | spec.md | in-review -> {status} | {by} | abc1234\n"


def write_revision(root, name, content):
    d = os.path.join(root, "work", "demo", "revisions")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name), "w", encoding="utf-8") as f:
        f.write(content)


class SignRefusals(unittest.TestCase):
    """Every refusal in spec R-7 / the interfaces: exit 3 with no CLAUDECODE, exit 1 otherwise,
    and nothing written to the target artifact on any refusal."""

    def test_refuses_outside_an_agent_session(self):
        with tempfile.TemporaryDirectory() as root:
            make_repo(root)
            r = run(root, "demo", "spec.md", claudecode=False)
            self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
            self.assertIn("status: in-review", read(root, "work/demo/spec.md"))

    def test_refuses_when_policy_missing(self):
        with tempfile.TemporaryDirectory() as root:
            make_repo(root, write_policy=False)
            r = run(root, "demo", "spec.md")
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("delegation", r.stderr.lower())
            self.assertIn("status: in-review", read(root, "work/demo/spec.md"))

    def test_refuses_artifact_outside_signable(self):
        # R-7: the policy's `signable` list, not only the hard-coded intent.md stop, decides which
        # artifact an agent may sign.
        with tempfile.TemporaryDirectory() as root:
            narrow = TEMPLATE_POLICY_TEXT.replace("signable: [spec.md, plan.md, incident.md]", "signable: [spec.md]", 1)
            make_repo(root, policy_content=narrow, spec_status="delegated", spec_by="claude")
            r = run(root, "demo", "plan.md")
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("signable", r.stderr)
            self.assertIn("status: in-review", read(root, "work/demo/plan.md"))

    def test_refuses_when_policy_disabled(self):
        with tempfile.TemporaryDirectory() as root:
            disabled = TEMPLATE_POLICY_TEXT.replace("enabled: true", "enabled: false", 1)
            make_repo(root, policy_content=disabled)
            r = run(root, "demo", "spec.md")
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("status: in-review", read(root, "work/demo/spec.md"))

    def test_refuses_when_intent_not_approved(self):
        with tempfile.TemporaryDirectory() as root:
            make_repo(root, intent_status="in-review")
            r = run(root, "demo", "spec.md")
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("intent.md", r.stderr)

    def test_refuses_when_intent_mode_is_supervised(self):
        with tempfile.TemporaryDirectory() as root:
            make_repo(root, intent_mode="supervised")
            r = run(root, "demo", "spec.md")
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("mode", r.stderr.lower())

    def test_refuses_intent_md_itself_as_a_target(self):
        # D-b: intent.md is never signable -- the file that carries the grant is never the file
        # the agent signs, delegated mode enabled and granted notwithstanding.
        with tempfile.TemporaryDirectory() as root:
            make_repo(root)
            r = run(root, "demo", "intent.md")
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("intent.md", r.stderr)
            text = read(root, "work/demo/intent.md")
            self.assertIn("status: approved", text)
            self.assertNotIn("status: delegated", text)

    def test_refuses_a_human_handle(self):
        with tempfile.TemporaryDirectory() as root:
            make_repo(root)
            r = run(root, "demo", "spec.md", handle="luissiviero")
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("luissiviero", r.stderr)
            self.assertIn("status: in-review", read(root, "work/demo/spec.md"))

    def test_refuses_when_predecessor_is_not_ready(self):
        # plan.md's predecessor is spec.md; the fixture default leaves spec.md 'in-review'.
        with tempfile.TemporaryDirectory() as root:
            make_repo(root)
            r = run(root, "demo", "plan.md")
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("spec.md", r.stderr)
            self.assertIn("status: in-review", read(root, "work/demo/plan.md"))

    def test_refuses_resign_without_revision(self):
        for status in ("approved", "delegated"):
            with self.subTest(status=status):
                with tempfile.TemporaryDirectory() as root:
                    by = "luissiviero" if status == "approved" else "claude"
                    make_repo(root, spec_status=status, spec_by=by, extra_log=_spec_sign_line(status, by))
                    r = run(root, "demo", "spec.md")
                    self.assertEqual(r.returncode, 1, r.stdout)
                    self.assertIn("revision", r.stderr.lower())
                    self.assertEqual(f"status: {status}" in read(root, "work/demo/spec.md"), True)

    def test_refuses_revision_record_missing(self):
        with tempfile.TemporaryDirectory() as root:
            make_repo(root, spec_status="delegated", spec_by="claude", extra_log=_spec_sign_line("delegated", "claude"))
            r = run(root, "demo", "spec.md", "--revision", "revisions/9.md")
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("revisions/9.md", r.stderr)

    def test_refuses_revision_with_one_reviewer(self):
        with tempfile.TemporaryDirectory() as root:
            make_repo(root, spec_status="delegated", spec_by="claude", extra_log=_spec_sign_line("delegated", "claude"))
            write_revision(root, "1.md", REVISION_ONE_REVIEWER)
            r = run(root, "demo", "spec.md", "--revision", "revisions/1.md")
            self.assertEqual(r.returncode, 1, r.stdout)

    def test_refuses_revision_with_a_keep_verdict(self):
        with tempfile.TemporaryDirectory() as root:
            make_repo(root, spec_status="delegated", spec_by="claude", extra_log=_spec_sign_line("delegated", "claude"))
            write_revision(root, "1.md", REVISION_ONE_KEEP)
            r = run(root, "demo", "spec.md", "--revision", "revisions/1.md")
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("keep", r.stderr.lower())


class SignPasses(unittest.TestCase):
    """The write side: front matter, ledger line, handle handling."""

    def test_signs_spec_and_appends_a_parseable_ledger_line(self):
        with tempfile.TemporaryDirectory() as root:
            make_repo(root)
            r = run(root, "demo", "spec.md", "--note", "looks good")
            self.assertEqual(r.returncode, 0, r.stderr)
            text = read(root, "work/demo/spec.md")
            self.assertIn("status: delegated", text)
            self.assertIn("approved-by: claude", text)
            self.assertRegex(text, r"approved-on: \d{4}-\d{2}-\d{2}")

            entries, malformed = log_ledger.parse(os.path.join(root, "work", "demo", "log.md"))
            self.assertEqual(malformed, [])
            sigs = log_ledger.signatures(entries, "spec.md")
            self.assertEqual(len(sigs), 1, entries)
            self.assertEqual(sigs[0].actor, "claude")
            self.assertEqual(sigs[0].from_status, "in-review")
            self.assertEqual(sigs[0].note, "looks good")

    def test_signs_plan_with_claude_bot_handle_from_env(self):
        with tempfile.TemporaryDirectory() as root:
            make_repo(root, spec_status="delegated", spec_by="claude", extra_log=_spec_sign_line("delegated", "claude"))
            r = run(root, "demo", "plan.md", handle="claude[bot]")
            self.assertEqual(r.returncode, 0, r.stderr)
            text = read(root, "work/demo/plan.md")
            self.assertIn("status: delegated", text)
            self.assertIn("approved-by: claude[bot]", text)
            entries, _ = log_ledger.parse(os.path.join(root, "work", "demo", "log.md"))
            sigs = log_ledger.signatures(entries, "plan.md")
            self.assertEqual(len(sigs), 1)
            self.assertEqual(sigs[0].actor, "claude[bot]")

    def test_signs_plan_when_spec_is_superseded(self):
        # The predecessor accepts approved, delegated OR superseded (spec R-7/D3).
        with tempfile.TemporaryDirectory() as root:
            make_repo(root, spec_status="superseded", spec_by="luissiviero")
            r = run(root, "demo", "plan.md")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("status: delegated", read(root, "work/demo/plan.md"))

    def test_resigns_with_a_unanimous_revision_record(self):
        with tempfile.TemporaryDirectory() as root:
            make_repo(root, spec_status="delegated", spec_by="claude", extra_log=_spec_sign_line("delegated", "claude"))
            write_revision(root, "1.md", REVISION_TWO_REVIEWERS_REVISE)
            r = run(root, "demo", "spec.md", "--revision", "revisions/1.md", "--note", "fixed X")
            self.assertEqual(r.returncode, 0, r.stderr)
            text = read(root, "work/demo/spec.md")
            self.assertIn("status: delegated", text)
            self.assertIn("approved-by: claude", text)

            entries, malformed = log_ledger.parse(os.path.join(root, "work", "demo", "log.md"))
            self.assertEqual(malformed, [])
            sigs = log_ledger.signatures(entries, "spec.md")
            self.assertEqual(len(sigs), 2, entries)
            self.assertEqual(sigs[-1].from_status, "delegated")
            self.assertTrue(sigs[-1].note.strip().startswith("revision 1:"), sigs[-1].note)
            self.assertIn("fixed X", sigs[-1].note)


if __name__ == "__main__":
    unittest.main()
