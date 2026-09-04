"""Bash-branch coverage for require-plan.sh and protect-tests.sh, and the control-plane unlock on
the edit branch of protect-paths.sh (knowledge/decisions/self-hooks-on.md; roadmap item 17).

Before this change the two plan hooks were registered on the edit tools only and exited 0 on an
empty file_path, so `cat > src/a.ts <<EOF` needed no approved plan and `sed -i` on a test file
during a `kind: fix` task was never refused. Both now walk bash_write_candidates() from _lib.sh,
the same parser protect-paths.sh uses. The unlock used to short-circuit the Bash branch only; it
now applies per protected path on both branches and never lifts the secret-material check.

The hooks are driven as subprocesses through scripts/hooktest.py (fake_repo + run_hook), which
strips SDLC_* from the environment first, so the kit repo's own settings.json unlock cannot leak
into these expectations.
"""
import json
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hooktest import fake_repo, run_hook  # noqa: E402

PLAN_IN_REVIEW = {"work/foo/plan.md": "---\nstatus: in-review\n---\n"}
PLAN_APPROVED = {"work/foo/plan.md": "---\nstatus: approved\napproved-by: luissiviero\n---\n"}
PLAN_FIX = {"work/foo/plan.md": "---\nstatus: approved\napproved-by: luissiviero\nkind: fix\n---\n"}
PLAN_FEATURE = {"work/foo/plan.md": "---\nstatus: approved\napproved-by: luissiviero\nkind: feature\n---\n"}
FOO = {"SDLC_WORK_ITEM": "foo"}

# A complete .sdlc/config.env for the two plan hooks with the Bash branch switched off.
GUARD_OFF_CONFIG = (
    'PLAN_REQUIRED_PATHS="src lib app services packages"\n'
    'TEST_FILE_GLOBS="*_test.* *.test.* *_spec.* *.spec.* test_*.py tests/* test/* __tests__/*"\n'
    'BASH_WRITE_GUARD="0"\n'
)

HEREDOC_INTO_SRC = "cat > src/a.ts <<'EOF'\nexport {}\nEOF"


def bash(command):
    return {
        "session_id": "test-session",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }


def edit(path):
    return {
        "session_id": "test-session",
        "hook_event_name": "PreToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": path, "old_string": "a", "new_string": "b"},
    }


def log_lines(root):
    """Lines of the fake repo's .sdlc/hook-decisions.log, split into their six fields."""
    path = os.path.join(root, ".sdlc", "hook-decisions.log")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [line.split("\t") for line in f.read().splitlines()]


class RequirePlanBashBranch(unittest.TestCase):
    HOOK = "require-plan.sh"

    def test_blocks_heredoc_into_src_when_plan_in_review(self):
        with fake_repo(**PLAN_IN_REVIEW) as root:
            r = run_hook(self.HOOK, bash(HEREDOC_INTO_SRC), root, env=FOO)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("in-review", r.stderr)
            self.assertIn("Bash command", r.stderr)

    def test_blocks_sed_in_place_on_src_when_plan_missing(self):
        with fake_repo() as root:
            r = run_hook(self.HOOK, bash("sed -i 's/a/b/' src/a.ts"), root, env={"SDLC_WORK_ITEM": "nope"})
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("does not exist", r.stderr)

    def test_blocks_cd_relative_write_into_src(self):
        with fake_repo(**PLAN_IN_REVIEW) as root:
            r = run_hook(self.HOOK, bash("cd src && echo x > a.ts"), root, env=FOO)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("src/a.ts", r.stderr)

    def test_allows_heredoc_into_src_when_plan_approved(self):
        with fake_repo(**PLAN_APPROVED) as root:
            r = run_hook(self.HOOK, bash(HEREDOC_INTO_SRC), root, env=FOO)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_allows_read_only_command_on_src(self):
        with fake_repo() as root:
            r = run_hook(self.HOOK, bash("grep -rn TODO src/ 2>&1 | head"), root, env={"SDLC_WORK_ITEM": "nope"})
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_allows_write_outside_plan_required_paths(self):
        with fake_repo() as root:
            r = run_hook(self.HOOK, bash("cat > docs/x.md <<'EOF'\nhi\nEOF"), root, env={"SDLC_WORK_ITEM": "nope"})
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_bash_write_guard_zero_disables_the_branch(self):
        with fake_repo(config_env=GUARD_OFF_CONFIG) as root:
            r = run_hook(self.HOOK, bash(HEREDOC_INTO_SRC), root, env={"SDLC_WORK_ITEM": "nope"})
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_edit_branch_unchanged(self):
        with fake_repo(**PLAN_IN_REVIEW) as root:
            r = run_hook(self.HOOK, edit("src/a.ts"), root, env=FOO)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertNotIn("Bash command", r.stderr)


class ProtectTestsBashBranch(unittest.TestCase):
    HOOK = "protect-tests.sh"

    def test_blocks_sed_in_place_on_test_file_during_fix(self):
        with fake_repo(**PLAN_FIX) as root:
            r = run_hook(self.HOOK, bash("sed -i 's/expect/skip/' src/foo.test.ts"), root, env=FOO)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("kind: fix", r.stderr)
            self.assertIn("Bash command", r.stderr)

    def test_blocks_redirect_into_tests_dir_during_fix(self):
        with fake_repo(**PLAN_FIX) as root:
            r = run_hook(self.HOOK, bash("cat > tests/test_a.py <<'EOF'\npass\nEOF"), root, env=FOO)
            self.assertEqual(r.returncode, 2, r.stderr)

    def test_allows_reading_test_file_during_fix(self):
        with fake_repo(**PLAN_FIX) as root:
            r = run_hook(self.HOOK, bash("cat src/foo.test.ts | head"), root, env=FOO)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_allows_writing_non_test_file_during_fix(self):
        with fake_repo(**PLAN_FIX) as root:
            r = run_hook(self.HOOK, bash("cat > src/foo.ts <<'EOF'\nexport {}\nEOF"), root, env=FOO)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_allows_test_write_when_kind_feature(self):
        with fake_repo(**PLAN_FEATURE) as root:
            r = run_hook(self.HOOK, bash("sed -i 's/a/b/' src/foo.test.ts"), root, env=FOO)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_bash_write_guard_zero_disables_the_branch(self):
        with fake_repo(config_env=GUARD_OFF_CONFIG, **PLAN_FIX) as root:
            r = run_hook(self.HOOK, bash("sed -i 's/a/b/' src/foo.test.ts"), root, env=FOO)
            self.assertEqual(r.returncode, 0, r.stderr)


class UnlockOnEditBranch(unittest.TestCase):
    """SDLC_CONTROL_PLANE_UNLOCK used to cover Bash writes only; the kit repo relies on it for
    its own maintenance through Edit and Write too (self-hooks-on.md)."""

    HOOK = "protect-paths.sh"
    UNLOCK = {"SDLC_CONTROL_PLANE_UNLOCK": "1"}

    def test_unlock_allows_edit_under_protected_path_with_audit_line(self):
        with fake_repo() as root:
            r = run_hook(self.HOOK, edit(".sdlc/x"), root, env=self.UNLOCK)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("unlocked", r.stderr)
            self.assertIn(".sdlc/x", r.stderr)

    def test_unlock_allows_bash_write_with_one_audit_line_per_target(self):
        with fake_repo() as root:
            r = run_hook(self.HOOK, bash("echo a > .sdlc/x && echo b >> .claude/hooks/y.sh"), root, env=self.UNLOCK)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stderr.count("unlocked"), 2, r.stderr)

    def test_unlock_does_not_lift_secret_material_check_on_edit(self):
        with fake_repo() as root:
            r = run_hook(self.HOOK, edit(".env"), root, env=self.UNLOCK)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("secret material", r.stderr)

    def test_unlock_does_not_lift_secret_material_check_on_bash(self):
        with fake_repo() as root:
            r = run_hook(self.HOOK, bash("cat > .env <<'EOF'\nX=1\nEOF"), root, env=self.UNLOCK)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("secret material", r.stderr)

    def test_unlock_leaves_unprotected_paths_silent(self):
        with fake_repo() as root:
            r = run_hook(self.HOOK, edit("docs/x.md"), root, env=self.UNLOCK)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stderr, "")
            self.assertEqual(r.stdout, "", "nothing unlocked: no systemMessage either")
            self.assertEqual(log_lines(root), [])

    def test_unlock_appends_log_line(self):
        with fake_repo() as root:
            r = run_hook(self.HOOK, edit(".sdlc/x"), root, env=self.UNLOCK)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("unlocked", r.stderr)  # the stderr line is unchanged
            lines = log_lines(root)
            self.assertEqual(len(lines), 1, lines)
            self.assertEqual(lines[0][1:], ["unlock", "protect-paths.sh", "Edit", "test-session", ".sdlc/x"])

    def test_unlock_emits_one_system_message_for_two_targets(self):
        with fake_repo() as root:
            r = run_hook(self.HOOK, bash("echo a > .sdlc/x && echo b >> .claude/hooks/y.sh"), root, env=self.UNLOCK)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stderr.count("unlocked"), 2, r.stderr)
            out = json.loads(r.stdout)  # exactly one JSON object on stdout
            self.assertEqual(set(out), {"systemMessage"})
            self.assertIn(".sdlc/x", out["systemMessage"])
            self.assertIn(".claude/hooks/y.sh", out["systemMessage"])
            self.assertIn("hook-decisions.log", out["systemMessage"])
            lines = log_lines(root)
            self.assertEqual([l[1] for l in lines], ["unlock", "unlock"])
            self.assertTrue(lines[0][5].startswith(".sdlc/x"), lines[0])
            self.assertTrue(lines[1][5].startswith(".claude/hooks/y.sh"), lines[1])

    def test_unlock_never_emits_permission_decision(self):
        with fake_repo() as root:
            r = run_hook(self.HOOK, edit(".sdlc/x"), root, env=self.UNLOCK)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertNotIn("permissionDecision", r.stdout)
            self.assertNotIn("hookSpecificOutput", r.stdout)
            self.assertEqual(list(json.loads(r.stdout)), ["systemMessage"])


class DecisionLog(unittest.TestCase):
    """Every block and ask lands in .sdlc/hook-decisions.log; a failed append changes nothing."""

    def test_block_is_logged(self):
        with fake_repo(**PLAN_IN_REVIEW) as root:
            r = run_hook("require-plan.sh", edit("src/a.ts"), root, env=FOO)
            self.assertEqual(r.returncode, 2, r.stderr)
            lines = log_lines(root)
            self.assertEqual(len(lines), 1, lines)
            self.assertEqual(lines[0][1:5], ["block", "require-plan.sh", "Edit", "test-session"])
            self.assertIn("in-review", lines[0][5])

    def test_ask_is_logged(self):
        with fake_repo() as root:
            with open(os.path.join(root, "f.txt"), "w", encoding="utf-8") as f:
                f.write("x")
            subprocess.run(["git", "-C", root, "add", "."], check=True)
            subprocess.run(["git", "-C", root, "commit", "-q", "-m", "init"], check=True)
            r = run_hook("production-gate.sh", bash("terraform apply"), root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn('"ask"', r.stdout)
            lines = log_lines(root)
            self.assertEqual(len(lines), 1, lines)
            self.assertEqual(lines[0][1:5], ["ask", "production-gate.sh", "Bash", "test-session"])

    @unittest.skipIf(os.name == "nt", "POSIX permissions")
    def test_read_only_sdlc_does_not_break_hook(self):
        with fake_repo(**PLAN_IN_REVIEW) as root:
            sdlc = os.path.join(root, ".sdlc")
            # A directory at the log path defeats the append for every user (root ignores a
            # read-only bit); the chmod covers the unprivileged case as well.
            os.makedirs(os.path.join(sdlc, "hook-decisions.log"))
            os.chmod(sdlc, 0o555)
            try:
                r = run_hook("require-plan.sh", edit("src/a.ts"), root, env=FOO)
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertIn("in-review", r.stderr)
                self.assertEqual(r.stderr.count("\n"), 1, r.stderr)
                r = run_hook("protect-paths.sh", edit(".sdlc/x"), root, env={"SDLC_CONTROL_PLANE_UNLOCK": "1"})
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn("unlocked", r.stderr)
                self.assertIn("systemMessage", r.stdout)
            finally:
                os.chmod(sdlc, 0o755)


class NeverUnlock(unittest.TestCase):
    """Three human-only files the unlock never covers: the release authorizations, the approvers
    file and the decision log (spec R-5, design D4)."""

    HOOK = "protect-paths.sh"
    UNLOCK = {"SDLC_CONTROL_PLANE_UNLOCK": "1"}

    def _blocked(self, root, payload):
        r = run_hook(self.HOOK, payload, root, env=self.UNLOCK)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("human-only", r.stderr)
        self.assertNotIn("unlocked", r.stderr)
        self.assertEqual(r.stdout, "")
        return r

    def test_release_authorizations_blocked_under_unlock(self):
        with fake_repo() as root:
            self._blocked(root, edit(".sdlc/release-authorizations/abc1234"))
            self._blocked(root, edit(".sdlc/release-authorizations"))
            self.assertEqual([l[1] for l in log_lines(root)], ["block", "block"])

    def test_approvers_yaml_blocked_under_unlock(self):
        with fake_repo() as root:
            self._blocked(root, edit(".sdlc/approvers.yaml"))

    def test_decision_log_blocked_under_unlock(self):
        with fake_repo() as root:
            self._blocked(root, edit(".sdlc/hook-decisions.log"))

    def test_bash_redirect_into_release_authorizations_blocked_under_unlock(self):
        with fake_repo() as root:
            self._blocked(root, bash("printf 'approved-by: me\\n' > .sdlc/release-authorizations/abc1234"))
            self._blocked(root, bash("cd .sdlc && cat > approvers.yaml <<'EOF'\nroles:\nEOF"))


if __name__ == "__main__":
    unittest.main()
