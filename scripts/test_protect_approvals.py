"""protect-approvals.sh: only a human flips a chain artifact to approved (work/approval-gate).

An agent may draft, revise and set `status: in-review` on work/<slug>/{intent,spec,plan,incident}.md,
but never `status: approved|superseded`, `approved-by:` or `approved-on:` (spec R-1, R-2), never
runs scripts/approve.py or unsets CLAUDECODE (R-3), and cannot route the same change through a
Bash write (R-4). The human unlock changes no verdict (R-5).

The hook is driven as a subprocess through scripts/hooktest.py (fake_repo + run_hook), which strips
SDLC_* from the environment first, so the kit repo's own settings.json unlock cannot leak in.
Builders follow scripts/test_bash_plan_gates.py.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hooktest import REAL_ROOT, fake_repo, run_hook  # noqa: E402

HOOK = "protect-approvals.sh"
DRAFT_INTENT = {"work/foo/intent.md": "---\nstatus: draft\napproved-by:\napproved-on:\n---\n# Intent\n"}
APPROVED_PLAN = {
    "work/foo/plan.md": "---\nstatus: approved\napproved-by: luissiviero\napproved-on: 2026-09-04\n---\n# Plan\n"
}
# BASH_WRITE_GUARD off: the two cheap Bash rules must still fire (spec D4).
GUARD_OFF_CONFIG = (
    'PLAN_REQUIRED_PATHS="src lib app services packages"\n'
    'TEST_FILE_GLOBS="*_test.* *.test.* *_spec.* *.spec.* test_*.py tests/* test/* __tests__/*"\n'
    'BASH_WRITE_GUARD="0"\n'
)


def _payload(tool, tool_input):
    return {
        "session_id": "test-session",
        "hook_event_name": "PreToolUse",
        "tool_name": tool,
        "tool_input": tool_input,
    }


def bash(command):
    return _payload("Bash", {"command": command})


def edit(path, new_string, old_string="a"):
    return _payload("Edit", {"file_path": path, "old_string": old_string, "new_string": new_string})


def write(path, content):
    return _payload("Write", {"file_path": path, "content": content})


def multiedit(path, edits):
    return _payload("MultiEdit", {"file_path": path, "edits": [{"old_string": o, "new_string": n} for o, n in edits]})


def template(name):
    with open(os.path.join(REAL_ROOT, "docs", "sdlc", "templates", name), encoding="utf-8") as f:
        return f.read()


class EditBranch(unittest.TestCase):
    """R-1, R-2, R-5: Edit/Write/MultiEdit on a chain artifact."""

    def test_blocks_status_approved(self):
        with fake_repo(**DRAFT_INTENT) as root:
            r = run_hook(HOOK, edit("work/foo/intent.md", "status: approved", "status: draft"), root)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("status: approved", r.stderr)
            self.assertIn("Only a human approves", r.stderr)

    def test_blocks_approved_by(self):
        with fake_repo(**DRAFT_INTENT) as root:
            r = run_hook(HOOK, edit("work/foo/intent.md", "approved-by: luissiviero"), root)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("approved-by", r.stderr)

    def test_blocks_write_of_superseded_artifact(self):
        content = template("intent.md").replace("\nstatus: draft", "\nstatus: superseded", 1)  # not the comment line
        self.assertIn("status: superseded", content)
        with fake_repo(**DRAFT_INTENT) as root:
            r = run_hook(HOOK, write("work/foo/intent.md", content), root)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("superseded", r.stderr)

    def test_blocks_multiedit_whose_second_edit_sets_approved_on(self):
        with fake_repo(**DRAFT_INTENT) as root:
            payload = multiedit("work/foo/intent.md", [("# Intent", "# Intent (v2)"), ("approved-on:", "approved-on: 2026-09-04")])
            r = run_hook(HOOK, payload, root)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("approved-on", r.stderr)

    def test_allows_status_in_review(self):
        with fake_repo(**DRAFT_INTENT) as root:
            r = run_hook(HOOK, edit("work/foo/intent.md", "status: in-review", "status: draft"), root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout, "")

    def test_allows_verbatim_template_draft(self):
        with fake_repo() as root:
            r = run_hook(HOOK, write("work/foo/intent.md", template("intent.md")), root)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_allows_edit_that_repeats_current_approval_values(self):
        # An approved plan's deviations log stays editable (spec D1): unchanged values are not a change.
        with fake_repo(**APPROVED_PLAN) as root:
            new = "status: approved\napproved-by: luissiviero\napproved-on: 2026-09-04\n"
            r = run_hook(HOOK, edit("work/foo/plan.md", new), root)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_allows_file_outside_artifact_pattern(self):
        with fake_repo(**{"docs/x.md": "---\nstatus: draft\n---\n"}) as root:
            r = run_hook(HOOK, edit("docs/x.md", "status: approved\napproved-by: luissiviero"), root)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_unlock_set_still_blocks(self):
        with fake_repo(**DRAFT_INTENT) as root:
            payload = edit("work/foo/intent.md", "status: approved", "status: draft")
            r = run_hook(HOOK, payload, root, env={"SDLC_CONTROL_PLANE_UNLOCK": "1"})
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertNotIn("unlock", r.stderr.lower())


class BashBranch(unittest.TestCase):
    """R-3, R-4: the same act routed through a Bash command."""

    def test_blocks_approve_py(self):
        with fake_repo(**DRAFT_INTENT) as root:
            r = run_hook(HOOK, bash("python3 scripts/approve.py foo intent.md --as luissiviero"), root)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("approve.py", r.stderr)

    def test_blocks_env_unset_claudecode(self):
        with fake_repo(**DRAFT_INTENT) as root:
            r = run_hook(HOOK, bash("env -u CLAUDECODE python3 scripts/approve.py foo plan.md"), root)
            self.assertEqual(r.returncode, 2, r.stderr)

    def test_blocks_claudecode_reassignment(self):
        with fake_repo(**DRAFT_INTENT) as root:
            r = run_hook(HOOK, bash("CLAUDECODE= python3 scripts/x.py"), root)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("CLAUDECODE", r.stderr)

    def test_approve_py_blocked_with_write_guard_off(self):
        with fake_repo(config_env=GUARD_OFF_CONFIG, **DRAFT_INTENT) as root:
            r = run_hook(HOOK, bash("python3 scripts/approve.py foo intent.md --as luissiviero"), root)
            self.assertEqual(r.returncode, 2, r.stderr)

    def test_blocks_sed_in_place_approval(self):
        with fake_repo(**DRAFT_INTENT) as root:
            r = run_hook(HOOK, bash("sed -i 's/draft/approved/' work/foo/intent.md"), root)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("work/foo/intent.md", r.stderr)

    def test_blocks_heredoc_writing_approved_plan(self):
        cmd = "cat > work/foo/plan.md <<'EOF'\n---\nstatus: approved\napproved-by: luissiviero\n---\nEOF"
        with fake_repo(**DRAFT_INTENT) as root:
            r = run_hook(HOOK, bash(cmd), root)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("work/foo/plan.md", r.stderr)

    def test_allows_read_only_command(self):
        with fake_repo(**APPROVED_PLAN) as root:
            r = run_hook(HOOK, bash("cat work/foo/plan.md"), root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout, "")

    def test_allows_draft_write_that_never_mentions_approval(self):
        cmd = "cat > work/foo/spec.md <<'EOF'\n---\nstatus: draft\n---\n# Spec\nEOF"
        with fake_repo(**DRAFT_INTENT) as root:
            r = run_hook(HOOK, bash(cmd), root)
            self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
