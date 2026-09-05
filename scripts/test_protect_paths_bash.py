"""Bash-branch tests for protect-paths.sh, plus MultiEdit/Bash coverage for block-secrets.sh.

Defect 4 in work/sdlc-kit-phase-1/plan.md: the PreToolUse edit hooks only matched
``Edit|Write|MultiEdit``, so a Bash heredoc (``cat > .sdlc/config.env <<'EOF'``)
walked straight past protect-paths.sh, block-secrets.sh, require-plan.sh and
protect-tests.sh. T11 closes that: protect-paths.sh grows a Bash branch built on
``bash_write_targets()``, block-secrets.sh scans ``edits[].new_string`` and
``command`` as well, and both are wired into the ``Bash`` matcher in
.claude/settings.json.

The hooks are driven as subprocesses through scripts/hooktest.py, exactly as
scripts/test_hooks_baseline.py does; that file's assertions must keep passing
unchanged (one of them is re-asserted here as a regression guard, because the
Bash branch required restructuring the $FILE branch's early exit).

Design note on the oracle: the guard is a heuristic over shell text, and it is
deliberately over-inclusive. A false positive costs one stderr line and the
agent retries with the Write tool; a false negative costs the control plane.
So the "allowed" cases below assert only what must never break -- reads,
pipelines, stderr redirection and writes outside the protected prefixes.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hooktest import fake_repo, run_hook  # noqa: E402

HOOK = "protect-paths.sh"
SECRETS_HOOK = "block-secrets.sh"

# Built at runtime (not as one literal) so this test file itself does not
# contain a string block-secrets.sh would flag when Claude Code writes it.
FAKE_AWS_KEY = "AKIA" + "ABCDEFGHIJKLMNOP"

# A .sdlc/config.env with the guard switched off. protect-paths.sh reads only
# PROTECTED_PATHS and BASH_WRITE_GUARD, so this is a complete config for it.
GUARD_OFF_CONFIG = (
    'PROTECTED_PATHS=".claude/hooks .github/workflows .sdlc"\n'
    'BASH_WRITE_GUARD="0"\n'
)

HEREDOC_INTO_SDLC = "cat > .sdlc/config.env <<'EOF'\nx\nEOF"


def bash(command):
    """A PreToolUse payload for the Bash tool (see scripts/fixtures/hook_inputs/bash.json)."""
    return {
        "session_id": "test-session",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }


def multiedit(*new_strings):
    """A PreToolUse payload for MultiEdit (see scripts/fixtures/hook_inputs/multiedit.json)."""
    return {
        "session_id": "test-session",
        "hook_event_name": "PreToolUse",
        "tool_name": "MultiEdit",
        "tool_input": {
            "file_path": "src/example.ts",
            "edits": [{"old_string": "old", "new_string": s} for s in new_strings],
        },
    }


class BashWriteGuardBlocks(unittest.TestCase):
    """Commands that write into PROTECTED_PATHS or to secret-looking filenames."""

    def _block(self, command, expected_fragment):
        with fake_repo() as root:
            result = run_hook(HOOK, bash(command), root)
            self.assertEqual(
                result.returncode,
                2,
                f"expected a block for {command!r}; got rc={result.returncode} "
                f"stdout={result.stdout!r} stderr={result.stderr!r}",
            )
            self.assertIn(expected_fragment, result.stderr)
            self.assertIn("Bash command", result.stderr)

    def test_blocks_heredoc_redirect_into_sdlc_config(self):
        self._block(HEREDOC_INTO_SDLC, ".sdlc/config.env")

    def test_blocks_append_into_hook_library(self):
        self._block("echo x >> .claude/hooks/_lib.sh", ".claude/hooks/_lib.sh")

    def test_blocks_tee_into_workflow(self):
        self._block(
            "tee -a .github/workflows/sdlc-gate.yml < /tmp/x",
            ".github/workflows/sdlc-gate.yml",
        )

    def test_blocks_sed_in_place_on_sdlc_active(self):
        self._block("sed -i s/a/b/ .sdlc/active", ".sdlc/active")

    def test_blocks_cp_into_hooks_directory(self):
        self._block("cp /tmp/x .claude/hooks/y.sh", ".claude/hooks/y.sh")

    def test_blocks_redirect_to_secret_filename(self):
        # Not under PROTECTED_PATHS: caught by the secret-filename case, the same
        # one the $FILE branch applies to Edit/Write.
        self._block("printf x > deploy.key", "deploy.key")

    def test_blocks_edit_of_verify_script(self):
        # work/loop-protection R-1: the verify loop is control plane; a file entry in
        # PROTECTED_PATHS matches as is on the Edit branch.
        payload = {
            "session_id": "test-session",
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "scripts/verify.sh", "old_string": "a", "new_string": "b"},
        }
        with fake_repo() as root:
            result = run_hook(HOOK, payload, root)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("scripts/verify.sh", result.stderr)
            self.assertNotIn("Bash command", result.stderr)

    def test_blocks_redirect_into_checks_dir(self):
        self._block("echo 'exit 0' > scripts/checks/zz.sh", "scripts/checks/zz.sh")

    def test_blocks_python_heredoc_that_opens_a_protected_path_for_writing(self):
        # `python3 - <<EOF` has no redirection target at all: the script *is* the
        # heredoc body, so the guard falls back to protected prefixes named
        # anywhere in the command plus open(<path>, 'w'|'a') targets.
        self._block(
            'python3 - <<\'EOF\'\nopen(".sdlc/x","w").write("1")\nEOF',
            ".sdlc",
        )


class BashWriteGuardAllows(unittest.TestCase):
    """Reads, pipelines and writes outside the protected prefixes must never block."""

    def _allow(self, command):
        with fake_repo() as root:
            result = run_hook(HOOK, bash(command), root)
            self.assertEqual(
                result.returncode,
                0,
                f"expected {command!r} to be allowed; stderr={result.stderr!r}",
            )

    def test_allows_redirect_outside_the_repo(self):
        self._allow("ls > /tmp/out")

    def test_allows_stderr_redirection_and_pipe(self):
        self._allow("scripts/verify.sh 2>&1 | tail -3")

    def test_allows_reading_a_protected_file(self):
        self._allow("cat .sdlc/config.env")

    def test_allows_grepping_a_protected_directory(self):
        self._allow("grep -r x .claude/hooks/")

    def test_allows_greater_than_inside_a_quoted_string(self):
        # The guard is a text heuristic, not a shell parser: it sees `> b` here
        # and offers `b` as a candidate target. `b` is under no protected prefix
        # and is not secret-shaped, so the command is allowed. This test pins the
        # outcome (allowed), not the parse.
        self._allow('echo "a > b"')

    def test_allows_git_diff_of_a_protected_file(self):
        self._allow("git diff -- .sdlc/config.env")


class BashWriteGuardSwitches(unittest.TestCase):
    """The two ways the guard stands down."""

    def test_bash_write_guard_zero_disables_the_branch(self):
        with fake_repo(config_env=GUARD_OFF_CONFIG) as root:
            result = run_hook(HOOK, bash(HEREDOC_INTO_SDLC), root)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_human_unlock_env_allows_and_logs_an_audit_line(self):
        # SDLC_CONTROL_PLANE_UNLOCK is only settable in the environment that
        # launched Claude Code; a Bash command an agent runs cannot set the
        # hook process's own environment. hooktest strips SDLC_* from the base
        # env, so this is the only thing under test here.
        with fake_repo() as root:
            result = run_hook(
                HOOK, bash(HEREDOC_INTO_SDLC), root, env={"SDLC_CONTROL_PLANE_UNLOCK": "1"}
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("unlocked", result.stderr)

    def test_edit_branch_still_blocks_protected_path(self):
        # Baseline re-assert: restructuring the $FILE early exit must not have
        # weakened the Edit/Write/MultiEdit branch (test_hooks_baseline.py owns
        # the full matrix).
        payload = {
            "session_id": "test-session",
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": ".sdlc/x", "old_string": "a", "new_string": "b"},
        }
        with fake_repo() as root:
            result = run_hook(HOOK, payload, root)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn(".sdlc/x", result.stderr)
            self.assertNotIn("Bash command", result.stderr)


class BlockSecretsWiderSurface(unittest.TestCase):
    """block-secrets.sh now reads edits[].new_string and command, not just content/new_string."""

    def test_blocks_key_in_multiedit_edits(self):
        with fake_repo() as root:
            payload = multiedit("const ok = 1;", f"const k = '{FAKE_AWS_KEY}';")
            result = run_hook(SECRETS_HOOK, payload, root)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("credential", result.stderr)

    def test_blocks_key_in_bash_heredoc_body(self):
        with fake_repo() as root:
            command = f"cat > src/keys.ts <<'EOF'\nexport const k = '{FAKE_AWS_KEY}';\nEOF"
            result = run_hook(SECRETS_HOOK, bash(command), root)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("credential", result.stderr)

    def test_allows_clean_multiedit(self):
        with fake_repo() as root:
            payload = multiedit("const a = 1;", "const k = process.env.API_KEY;")
            result = run_hook(SECRETS_HOOK, payload, root)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
