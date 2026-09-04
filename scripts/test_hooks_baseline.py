"""Characterisation tests: lock in today's behaviour of every hook in .claude/hooks/.

One class per hook. These tests exercise the hooks as external processes via
scripts/hooktest.py (fake_repo + run_hook) -- see that module's docstring for
the allow/block/ask contract. Fixtures in scripts/fixtures/hook_inputs/ supply
the PreToolUse payload shape per tool; tests load a fixture and override the
fields under test so a shape drift in the harness fixtures shows up as one
place to fix, not many.
"""
import json
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hooktest import REAL_ROOT, fake_repo, run_hook  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "hook_inputs")

# Built at runtime (not as one literal) so this test file itself does not
# contain a string block-secrets.sh would flag when Claude Code writes it.
FAKE_AWS_KEY = "AKIA" + "ABCDEFGHIJKLMNOP"


def load_fixture(name, **tool_input_overrides):
    with open(os.path.join(FIXTURES, f"{name}.json"), encoding="utf-8") as f:
        payload = json.load(f)
    payload["tool_input"].update(tool_input_overrides)
    return payload


class Harness(unittest.TestCase):
    """scripts/hooktest.py itself: what every fake repo carries (work/front-matter spec R-10)."""

    def test_fake_repo_carries_approvers_yaml(self):
        with open(os.path.join(REAL_ROOT, ".sdlc", "approvers.yaml"), encoding="utf-8") as f:
            real = f.read()
        with fake_repo() as root:
            with open(os.path.join(root, ".sdlc", "approvers.yaml"), encoding="utf-8") as f:
                self.assertEqual(f.read(), real)
        with fake_repo(approvers_yaml="roles:\n  tech-lead: [alice]\n") as root:
            with open(os.path.join(root, ".sdlc", "approvers.yaml"), encoding="utf-8") as f:
                self.assertEqual(f.read(), "roles:\n  tech-lead: [alice]\n")
        # A test's own file wins over the copy.
        with fake_repo(**{".sdlc/approvers.yaml": "roles:\n"}) as root:
            with open(os.path.join(root, ".sdlc", "approvers.yaml"), encoding="utf-8") as f:
                self.assertEqual(f.read(), "roles:\n")


class ProtectPathsHook(unittest.TestCase):
    HOOK = "protect-paths.sh"

    def _block(self, path):
        with fake_repo() as root:
            payload = load_fixture("edit", file_path=path)
            result = run_hook(self.HOOK, payload, root)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn(path, result.stderr)

    def test_blocks_sdlc_config(self):
        self._block(".sdlc/x")

    def test_blocks_github_workflow(self):
        self._block(".github/workflows/y.yml")

    def test_blocks_claude_hook(self):
        self._block(".claude/hooks/z.sh")

    def test_blocks_id_rsa(self):
        self._block("id_rsa")

    def test_blocks_dotenv(self):
        self._block(".env")

    def test_allows_source_file(self):
        with fake_repo() as root:
            payload = load_fixture("edit", file_path="src/a.ts")
            result = run_hook(self.HOOK, payload, root)
            self.assertEqual(result.returncode, 0, result.stderr)


class BlockSecretsHook(unittest.TestCase):
    HOOK = "block-secrets.sh"

    def test_blocks_akia_key_in_write_content(self):
        with fake_repo() as root:
            payload = load_fixture("write", content=FAKE_AWS_KEY)
            result = run_hook(self.HOOK, payload, root)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("credential", result.stderr)

    def test_blocks_akia_key_in_edit_new_string(self):
        with fake_repo() as root:
            payload = load_fixture("edit", new_string=FAKE_AWS_KEY)
            result = run_hook(self.HOOK, payload, root)
            self.assertEqual(result.returncode, 2, result.stderr)

    def test_allows_env_var_reference(self):
        with fake_repo() as root:
            payload = load_fixture("edit", new_string="process.env.API_KEY")
            result = run_hook(self.HOOK, payload, root)
            self.assertEqual(result.returncode, 0, result.stderr)


class RequirePlanHook(unittest.TestCase):
    HOOK = "require-plan.sh"

    def test_blocks_when_work_item_missing(self):
        with fake_repo() as root:
            payload = load_fixture("edit", file_path="src/a.ts")
            result = run_hook(self.HOOK, payload, root, env={"SDLC_WORK_ITEM": "nope"})
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("does not exist", result.stderr)

    def test_blocks_when_plan_in_review(self):
        with fake_repo(**{"work/foo/plan.md": "---\nstatus: in-review\n---\n"}) as root:
            payload = load_fixture("edit", file_path="src/a.ts")
            result = run_hook(self.HOOK, payload, root, env={"SDLC_WORK_ITEM": "foo"})
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("in-review", result.stderr)

    def test_allows_when_plan_approved(self):
        with fake_repo(**{"work/foo/plan.md": "---\nstatus: approved\napproved-by: luissiviero\n---\n"}) as root:
            payload = load_fixture("edit", file_path="src/a.ts")
            result = run_hook(self.HOOK, payload, root, env={"SDLC_WORK_ITEM": "foo"})
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_template_derived_plan_reads_clean_status(self):
        """A plan.md copied verbatim from docs/sdlc/templates/ reads as 'draft', not as
        'draft   # ...' (work/front-matter spec R-5): today's awk reader sees a bare value."""
        with open(os.path.join(REAL_ROOT, "docs", "sdlc", "templates", "plan.md"), encoding="utf-8") as f:
            template = f.read()
        with fake_repo(**{"work/foo/plan.md": template}) as root:
            payload = load_fixture("edit", file_path="src/a.ts")
            result = run_hook(self.HOOK, payload, root, env={"SDLC_WORK_ITEM": "foo"})
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("status 'draft', not 'approved'", result.stderr)
            self.assertNotIn("#", result.stderr)

    def test_allows_path_outside_plan_required_paths(self):
        with fake_repo() as root:
            payload = load_fixture("edit", file_path="docs/readme.md")
            result = run_hook(self.HOOK, payload, root, env={"SDLC_WORK_ITEM": "nope"})
            self.assertEqual(result.returncode, 0, result.stderr)


class ProtectTestsHook(unittest.TestCase):
    HOOK = "protect-tests.sh"

    def test_blocks_test_file_when_kind_fix(self):
        with fake_repo(**{"work/foo/plan.md": "---\nstatus: approved\napproved-by: luissiviero\nkind: fix\n---\n"}) as root:
            payload = load_fixture("edit", file_path="src/foo.test.ts")
            result = run_hook(self.HOOK, payload, root, env={"SDLC_WORK_ITEM": "foo"})
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("kind: fix", result.stderr)

    def test_allows_non_test_file_when_kind_fix(self):
        with fake_repo(**{"work/foo/plan.md": "---\nstatus: approved\napproved-by: luissiviero\nkind: fix\n---\n"}) as root:
            payload = load_fixture("edit", file_path="src/foo.ts")
            result = run_hook(self.HOOK, payload, root, env={"SDLC_WORK_ITEM": "foo"})
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_allows_test_file_when_kind_feature(self):
        with fake_repo(**{"work/foo/plan.md": "---\nstatus: approved\napproved-by: luissiviero\nkind: feature\n---\n"}) as root:
            payload = load_fixture("edit", file_path="src/foo.test.ts")
            result = run_hook(self.HOOK, payload, root, env={"SDLC_WORK_ITEM": "foo"})
            self.assertEqual(result.returncode, 0, result.stderr)


class ProductionGateHook(unittest.TestCase):
    HOOK = "production-gate.sh"

    def _head_sha(self, root):
        with open(os.path.join(root, "f.txt"), "w", encoding="utf-8") as f:
            f.write("x")
        subprocess.run(["git", "-C", root, "add", "."], check=True)
        subprocess.run(["git", "-C", root, "commit", "-q", "-m", "init"], check=True)
        return subprocess.run(
            ["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()

    def test_blocks_rm_rf_root(self):
        with fake_repo() as root:
            payload = load_fixture("bash", command="rm -rf /")
            result = run_hook(self.HOOK, payload, root)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("destructive", result.stderr)

    def test_asks_on_terraform_apply(self):
        with fake_repo() as root:
            self._head_sha(root)
            payload = load_fixture("bash", command="terraform apply")
            result = run_hook(self.HOOK, payload, root)
            self.assertEqual(result.returncode, 0, result.stderr)
            out = json.loads(result.stdout)
            self.assertEqual(
                out["hookSpecificOutput"]["permissionDecision"], "ask"
            )

    def test_blocks_terraform_apply_when_unattended(self):
        with fake_repo() as root:
            self._head_sha(root)
            payload = load_fixture("bash", command="terraform apply")
            result = run_hook(self.HOOK, payload, root, env={"SDLC_UNATTENDED": "1"})
            self.assertEqual(result.returncode, 2, result.stderr)

    def test_allows_terraform_apply_with_matching_release_approval(self):
        with fake_repo() as root:
            sha = self._head_sha(root)
            payload = load_fixture("bash", command="terraform apply")
            result = run_hook(self.HOOK, payload, root, env={"RELEASE_APPROVAL": sha})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_allows_plain_command(self):
        with fake_repo() as root:
            payload = load_fixture("bash", command="ls -la")
            result = run_hook(self.HOOK, payload, root)
            self.assertEqual(result.returncode, 0, result.stderr)

    # --- what the gate must see (review of PR #11) -------------------------------------------
    # The deploy clause used to be one regex whose boundary was `(^|[;&| ])` with a literal
    # space and whose push rule matched only a bare `main`-shaped word after `git push`. These
    # cases are the bypasses and the false positives that found.

    def _on_branch(self, root, branch):
        """Commit once, then put the fake repo on <branch>: a bare `git push` reads HEAD."""
        sha = self._head_sha(root)
        subprocess.run(["git", "-C", root, "branch", "-M", branch], check=True)
        return sha

    def _decision(self, root, command, env=None):
        """'allow' | 'ask' | 'block' for <command>, per the hook contract in hooktest.py."""
        result = run_hook(self.HOOK, load_fixture("bash", command=command), root, env=env)
        if result.returncode == 2:
            return "block"
        self.assertEqual(result.returncode, 0, result.stderr)
        if not result.stdout.strip():
            return "allow"
        return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]

    def test_asks_on_push_that_reaches_a_protected_branch(self):
        with fake_repo() as root:
            self._on_branch(root, "work/foo")
            for command in (
                "git push origin main",
                "git push origin HEAD:main",          # refspec
                "git push origin :main",              # deletes the remote branch
                "git push origin refs/heads/main",    # fully qualified ref
                "git push origin +main",              # forced refspec
                "git push origin --delete production",
                "git push --all origin",              # every local branch, main included
                "git push --mirror origin",
                "git -C /tmp/x push origin master",
                "(git push origin main)",             # wrapped in a subshell
            ):
                with self.subTest(command=command):
                    self.assertEqual(self._decision(root, command), "ask")

    def test_asks_on_bare_push_when_head_is_protected(self):
        with fake_repo() as root:
            self._on_branch(root, "main")
            # (a force push never reaches here: DANGER_RE blocks it outright)
            for command in ("git push", "git push origin", "git push --quiet"):
                with self.subTest(command=command):
                    self.assertEqual(self._decision(root, command), "ask")

    def test_allows_push_that_stays_on_a_feature_branch(self):
        with fake_repo() as root:
            self._on_branch(root, "work/foo")
            for command in (
                "git push",
                "git push origin work/foo",
                "git push -u origin HEAD:work/foo",
                "git log --grep=push",
            ):
                with self.subTest(command=command):
                    self.assertEqual(self._decision(root, command), "allow")

    def test_asks_when_a_deploy_starts_after_a_tab_or_a_paren(self):
        with fake_repo() as root:
            self._head_sha(root)
            for command in ("	terraform apply", "echo hi;	kubectl apply -f x.yaml", "(helm upgrade r c)"):
                with self.subTest(command=command):
                    self.assertEqual(self._decision(root, command), "ask")

    def test_allows_read_only_cloud_subcommands(self):
        with fake_repo() as root:
            self._on_branch(root, "work/foo")
            for command in (
                "az webapp list",
                "aws lambda list-functions",
                "aws ecs describe-services --cluster c",
                "aws cloudformation describe-stacks",
            ):
                with self.subTest(command=command):
                    self.assertEqual(self._decision(root, command), "allow")

    def test_asks_on_mutating_cloud_subcommands(self):
        with fake_repo() as root:
            self._head_sha(root)
            for command in (
                "aws lambda update-function-code --function-name f --zip-file x",
                "aws ecs update-service --service s",
                "aws cloudformation deploy --stack-name s",
                "az webapp deployment source config-zip --src x.zip",
            ):
                with self.subTest(command=command):
                    self.assertEqual(self._decision(root, command), "ask")


class PostEditFormatHook(unittest.TestCase):
    HOOK = "post-edit-format.sh"

    def test_noop_with_empty_format_cmd(self):
        with fake_repo() as root:
            payload = load_fixture("edit", file_path="src/a.ts")
            result = run_hook(self.HOOK, payload, root)
            self.assertEqual(result.returncode, 0, result.stderr)


class StopVerifyReminderHook(unittest.TestCase):
    HOOK = "stop-verify-reminder.sh"

    def test_clean_tree_is_silent(self):
        with fake_repo() as root:
            result = run_hook(self.HOOK, {"session_id": "s"}, root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_stop_hook_active_short_circuits(self):
        with fake_repo() as root:
            result = run_hook(self.HOOK, {"session_id": "s", "stop_hook_active": True}, root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
