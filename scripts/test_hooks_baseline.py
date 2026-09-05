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


# work/delegated-mode R-10: require-plan.sh's delegated branch opens the plan gate on a
# `status: delegated` plan.md the same way it opens on a tech-lead-approved one, but only under a
# human grant (mode: delegated on the item's intent.md) and an enabled policy that lists the
# signer among `agents` and plan.md among `signable`.
DELEGATION_POLICY = """\
enabled: true
agents: [claude, claude[bot]]
signable: [spec.md, plan.md, incident.md]
risk-classes: [low]
max-deviations: 5
revisions: consensus
min-reviewers: 2
merge:
  enabled: true
  require-review: true
  require-checks: [sdlc-gate, agent-evals, pr-review]
  method: merge
  cool-off-hours: 0
locked-paths: [scripts/check_artifact_chain.py]
"""
DELEGATED_INTENT = {
    "work/foo/intent.md": (
        "---\nstatus: approved\napproved-by: luissiviero\napproved-on: 2026-09-04\n"
        "risk-class: low\nmode: delegated\ndelegated-by: luissiviero\ndelegated-on: 2026-09-04\n"
        "---\n# Intent\n"
    )
}
SUPERVISED_INTENT = {
    "work/foo/intent.md": (
        "---\nstatus: approved\napproved-by: luissiviero\napproved-on: 2026-09-04\n"
        "risk-class: low\nmode: supervised\ndelegated-by:\ndelegated-on:\n"
        "---\n# Intent\n"
    )
}
DELEGATED_PLAN_CLAUDE = {"work/foo/plan.md": "---\nstatus: delegated\napproved-by: claude\n---\n# Plan\n"}
DELEGATED_PLAN_MALLORY = {"work/foo/plan.md": "---\nstatus: delegated\napproved-by: mallory\n---\n# Plan\n"}


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

    def test_verdict_ignores_caller_identity_fields(self):
        """The hooks read tool_name, tool_input, cwd and session_id and nothing about the caller, so a
        subagent's tool call meets the same gate as the lead's (knowledge/decisions/one-writer-until-ledger.md;
        work/delegation-boundary R-7)."""
        with fake_repo() as root:
            plain = load_fixture("edit", file_path=".sdlc/x")
            tagged = dict(plain, agent_name="implementer", subagent_type="implementer", parent_tool_use_id="toolu_01")
            a = run_hook(self.HOOK, plain, root)
            b = run_hook(self.HOOK, tagged, root)
            self.assertEqual(a.returncode, 2, a.stderr)
            self.assertEqual((a.returncode, a.stdout, a.stderr), (b.returncode, b.stdout, b.stderr))

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

    def test_blocks_notebook_under_sdlc(self):
        """work/bash-guard-hardening R-8: NotebookEdit's notebook_path takes the $FILE branch."""
        with fake_repo() as root:
            payload = load_fixture("notebookedit", notebook_path=".sdlc/x.ipynb")
            result = run_hook(self.HOOK, payload, root)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn(".sdlc/x.ipynb", result.stderr)

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

    # work/approval-gate R-6: an approved plan counts only when approved-by holds the plan's role
    # (artifacts.plan.md in .sdlc/approvers.yaml, tech-lead here) and is not in never-approve.
    def test_blocks_when_plan_approved_by_claude(self):
        with fake_repo(**{"work/foo/plan.md": "---\nstatus: approved\napproved-by: claude\n---\n"}) as root:
            payload = load_fixture("edit", file_path="src/a.ts")
            result = run_hook(self.HOOK, payload, root, env={"SDLC_WORK_ITEM": "foo"})
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("approved-by 'claude'", result.stderr)
            self.assertIn("tech-lead", result.stderr)

    def test_blocks_when_plan_approved_by_unlisted_handle(self):
        with fake_repo(**{"work/foo/plan.md": "---\nstatus: approved\napproved-by: someone-else\n---\n"}) as root:
            payload = load_fixture("edit", file_path="src/a.ts")
            result = run_hook(self.HOOK, payload, root, env={"SDLC_WORK_ITEM": "foo"})
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("someone-else", result.stderr)

    def test_blocks_when_approvers_file_missing(self):
        with fake_repo(**{"work/foo/plan.md": "---\nstatus: approved\napproved-by: luissiviero\n---\n"}) as root:
            os.remove(os.path.join(root, ".sdlc", "approvers.yaml"))
            payload = load_fixture("edit", file_path="src/a.ts")
            result = run_hook(self.HOOK, payload, root, env={"SDLC_WORK_ITEM": "foo"})
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("approvers.yaml", result.stderr)

    def test_allows_quoted_handle_with_at_and_capitals(self):
        with fake_repo(**{"work/foo/plan.md": '---\nstatus: approved\napproved-by: "@LuisSiviero"\n---\n'}) as root:
            payload = load_fixture("edit", file_path="src/a.ts")
            result = run_hook(self.HOOK, payload, root, env={"SDLC_WORK_ITEM": "foo"})
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_status_with_trailing_comment_is_read(self):
        """work/loop-protection R-6: require-plan.sh reads status: through fm_value."""
        plan = "---\nstatus: approved   # set by scripts/approve.py\napproved-by: luissiviero\n---\n"
        with fake_repo(**{"work/foo/plan.md": plan}) as root:
            payload = load_fixture("edit", file_path="src/a.ts")
            result = run_hook(self.HOOK, payload, root, env={"SDLC_WORK_ITEM": "foo"})
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_status_in_review_with_comment_blocks_with_clean_value(self):
        with fake_repo(**{"work/foo/plan.md": "---\nstatus: in-review # c\n---\n"}) as root:
            payload = load_fixture("edit", file_path="src/a.ts")
            result = run_hook(self.HOOK, payload, root, env={"SDLC_WORK_ITEM": "foo"})
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("status 'in-review'", result.stderr)
            self.assertNotIn("#", result.stderr)

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

    # -- work/delegated-mode R-10: the delegated branch --------------------------------------

    def test_allows_when_plan_delegated_with_grant(self):
        files = dict(DELEGATED_INTENT, **DELEGATED_PLAN_CLAUDE, **{".sdlc/delegation.yaml": DELEGATION_POLICY})
        with fake_repo(**files) as root:
            payload = load_fixture("edit", file_path="src/a.ts")
            result = run_hook(self.HOOK, payload, root, env={"SDLC_WORK_ITEM": "foo"})
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_blocks_when_plan_delegated_but_policy_missing(self):
        # No .sdlc/delegation.yaml: a signature with no policy behind it opens nothing.
        files = dict(DELEGATED_INTENT, **DELEGATED_PLAN_CLAUDE)
        with fake_repo(**files) as root:
            payload = load_fixture("edit", file_path="src/a.ts")
            result = run_hook(self.HOOK, payload, root, env={"SDLC_WORK_ITEM": "foo"})
            self.assertEqual(result.returncode, 2, result.stderr)

    def test_blocks_when_plan_delegated_by_handle_outside_agents(self):
        files = dict(DELEGATED_INTENT, **DELEGATED_PLAN_MALLORY, **{".sdlc/delegation.yaml": DELEGATION_POLICY})
        with fake_repo(**files) as root:
            payload = load_fixture("edit", file_path="src/a.ts")
            result = run_hook(self.HOOK, payload, root, env={"SDLC_WORK_ITEM": "foo"})
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("mallory", result.stderr)

    def test_blocks_when_intent_mode_is_supervised(self):
        files = dict(SUPERVISED_INTENT, **DELEGATED_PLAN_CLAUDE, **{".sdlc/delegation.yaml": DELEGATION_POLICY})
        with fake_repo(**files) as root:
            payload = load_fixture("edit", file_path="src/a.ts")
            result = run_hook(self.HOOK, payload, root, env={"SDLC_WORK_ITEM": "foo"})
            self.assertEqual(result.returncode, 2, result.stderr)

    def test_blocks_when_plan_not_in_signable(self):
        policy = DELEGATION_POLICY.replace("signable: [spec.md, plan.md, incident.md]", "signable: [spec.md, incident.md]")
        files = dict(DELEGATED_INTENT, **DELEGATED_PLAN_CLAUDE, **{".sdlc/delegation.yaml": policy})
        with fake_repo(**files) as root:
            payload = load_fixture("edit", file_path="src/a.ts")
            result = run_hook(self.HOOK, payload, root, env={"SDLC_WORK_ITEM": "foo"})
            self.assertEqual(result.returncode, 2, result.stderr)


FIX_PLAN = "---\nstatus: approved\napproved-by: luissiviero\nkind: fix\n---\n"
FEATURE_PLAN = "---\nstatus: approved\napproved-by: luissiviero\nkind: feature\n---\n"
# Under kind: fix only an EXISTING test is locked (work/loop-protection R-5): the fixtures that
# expect a block create the file first, the fixtures that expect an allow do not.
EXISTING_TEST = {"src/foo.test.ts": "it('x', () => {})\n"}


class ProtectTestsHook(unittest.TestCase):
    HOOK = "protect-tests.sh"

    def _run(self, files, path):
        with fake_repo(**files) as root:
            payload = load_fixture("edit", file_path=path)
            return run_hook(self.HOOK, payload, root, env={"SDLC_WORK_ITEM": "foo"})

    def test_blocks_existing_test_file_when_kind_fix(self):
        result = self._run({"work/foo/plan.md": FIX_PLAN, **EXISTING_TEST}, "src/foo.test.ts")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("kind: fix", result.stderr)
        self.assertIn("existing test file", result.stderr)

    def test_allows_new_test_file_when_kind_fix(self):
        result = self._run({"work/foo/plan.md": FIX_PLAN}, "src/new.test.ts")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_allows_new_eval_case_when_kind_fix(self):
        result = self._run({"work/foo/plan.md": FIX_PLAN}, "evals/cases/incident-42.yaml")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_blocks_existing_eval_case_when_kind_fix(self):
        result = self._run({"work/foo/plan.md": FIX_PLAN, "evals/cases/x.yaml": "name: x\n"}, "evals/cases/x.yaml")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("existing test file", result.stderr)

    def test_kind_with_trailing_comment_locks(self):
        plan = "---\nstatus: approved\napproved-by: luissiviero\nkind: fix   # feature | fix\n---\n"
        result = self._run({"work/foo/plan.md": plan, **EXISTING_TEST}, "src/foo.test.ts")
        self.assertEqual(result.returncode, 2, result.stderr)

    def test_quoted_kind_locks(self):
        plan = '---\nstatus: approved\napproved-by: luissiviero\nkind: "Fix"\n---\n'
        result = self._run({"work/foo/plan.md": plan, **EXISTING_TEST}, "src/foo.test.ts")
        self.assertEqual(result.returncode, 2, result.stderr)

    def test_capitalised_kind_locks(self):
        plan = "---\nstatus: approved\napproved-by: luissiviero\nkind: Fix\n---\n"
        result = self._run({"work/foo/plan.md": plan, **EXISTING_TEST}, "src/foo.test.ts")
        self.assertEqual(result.returncode, 2, result.stderr)

    def test_crlf_plan_locks(self):
        plan = "---\r\nstatus: approved\r\napproved-by: luissiviero\r\nkind: fix\r\n---\r\n"
        result = self._run({"work/foo/plan.md": plan, **EXISTING_TEST}, "src/foo.test.ts")
        self.assertEqual(result.returncode, 2, result.stderr)

    def test_allows_non_test_file_when_kind_fix(self):
        result = self._run({"work/foo/plan.md": FIX_PLAN}, "src/foo.ts")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_allows_test_file_when_kind_feature(self):
        result = self._run({"work/foo/plan.md": FEATURE_PLAN, **EXISTING_TEST}, "src/foo.test.ts")
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

    # --- work/deploy-gate: the authorization file is validated; more routes are deploy-shaped ---

    def _authorize(self, root, sha, body):
        d = os.path.join(root, ".sdlc", "release-authorizations")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, sha), "w", encoding="utf-8") as f:
            f.write(body)

    def _log_verdicts(self, root):
        path = os.path.join(root, ".sdlc", "hook-decisions.log")
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as f:
            return [line.split("\t")[1] for line in f.read().splitlines()]

    def test_allows_release_authorization_by_release_manager(self):
        with fake_repo() as root:
            sha = self._head_sha(root)
            self._authorize(root, sha, "approved-by: luissiviero\n")
            result = run_hook(self.HOOK, load_fixture("bash", command="terraform apply"), root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            self.assertIn("allow", self._log_verdicts(root))

    def test_asks_when_release_authorization_names_claude(self):
        with fake_repo() as root:
            sha = self._head_sha(root)
            self._authorize(root, sha, "---\napproved-by: claude\n---\n")
            self.assertEqual(self._decision(root, "terraform apply"), "ask")
            self.assertIn("reject", self._log_verdicts(root))

    def test_blocks_unattended_when_release_authorization_names_someone(self):
        with fake_repo() as root:
            sha = self._head_sha(root)
            self._authorize(root, sha, "approved-by: someone   # not a release-manager\n")
            result = run_hook(self.HOOK, load_fixture("bash", command="terraform apply"), root,
                              env={"SDLC_UNATTENDED": "1"})
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("reject", self._log_verdicts(root))
            self.assertIn("block", self._log_verdicts(root))

    def test_asks_on_deploy_shaped_commands(self):
        with fake_repo() as root:
            self._on_branch(root, "work/foo")
            for command in (
                "make deploy ENV=production",
                "./scripts/deploy.sh production",
                "gh workflow run deploy.yml -f environment=production",
                "./deploy production",
                "gh release create v1.0",
                "gh pr merge 5 --squash",
                "gh api -X POST repos/o/r/merges -f base=main",
            ):
                with self.subTest(command=command):
                    self.assertEqual(self._decision(root, command), "ask")

    def test_allows_deploy_lookalikes(self):
        with fake_repo() as root:
            self._on_branch(root, "work/foo")
            for command in (
                "deploy --help",
                "echo deployment notes",
                "gh pr view 12",
                "gh api repos/o/r/releases/latest",
                "git log --grep=deploy",
            ):
                with self.subTest(command=command):
                    self.assertEqual(self._decision(root, command), "allow")

    def test_asks_on_gh_pr_merge_admin(self):
        with fake_repo() as root:
            self._on_branch(root, "work/foo")
            self.assertEqual(self._decision(root, "gh pr merge --admin 12"), "ask")

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


class SettingsAllowList(unittest.TestCase):
    """work/delegated-mode R-11: the commands a delegated run needs are on the allow list of both
    settings files (the kit's own and the adopter template), and the deny list is untouched."""
    ENTRIES = ("Bash(python3 scripts/sign.py*)", "Bash(gh pr ready*)", "Bash(gh pr comment*)",
               "Bash(gh pr create*)", "Bash(git push -u origin claude/*)")
    DENY = ["Read(./.env)", "Read(./.env.*)", "Read(./secrets/**)", "Read(~/.ssh/**)", "Read(~/.aws/**)",
            "WebFetch", "Bash(curl *)", "Bash(wget *)"]

    def test_both_settings_files_allow_the_run_commands(self):
        for rel in (".claude/settings.json", "docs/sdlc/templates/claude-settings.json"):
            with open(os.path.join(REAL_ROOT, rel), encoding="utf-8") as f:
                perms = json.load(f)["permissions"]
            for entry in self.ENTRIES:
                self.assertIn(entry, perms["allow"], rel)
            self.assertEqual(perms["deny"], self.DENY, rel)
