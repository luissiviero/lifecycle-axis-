import os
import shutil
import stat
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
ADOPT_SH = os.path.join(HERE, "adopt.sh")

# A representative sample of what adopt.sh should place in a target, one path
# per category from the spec -- not the exhaustive list.
SAMPLE_FILES = [
    ".sdlc/config.env",
    ".sdlc/README.md",
    ".sdlc/approvers.yaml",
    ".sdlc/environments.yaml",
    ".sdlc/active",
    ".claude/skills/sdlc-intent/SKILL.md",
    ".claude/agents/explorer.md",
    "docs/sdlc/templates/intent.md",
    "docs/sdlc/rules/00-chain.md",
    "docs/sdlc/README.md",
    "docs/sdlc/okf-pairing.md",
    "scripts/verify.sh",
    "scripts/check_artifact_chain.py",
    "scripts/gen_context_files.py",
    "scripts/checks/context-drift.sh",
    "evals/README.md",
    "evals/cases/hook-protects-tests-during-fix.yaml",
    "work/_example/intent.md",
    ".github/workflows/sdlc-gate.yml",
    ".github/workflows/agent-evals.yml",
    ".github/CODEOWNERS",
    "REVIEW.md",
    "monitoring/bands.yaml",
    "knowledge/index.md",
    "knowledge/decisions/index.md",
    "CLAUDE.md",
    "GEMINI.md",
    "AGENTS.md",
]

HOOK_ONLY_FILES = [
    ".claude/settings.json",
    ".claude/hooks/protect-paths.sh",
    ".claude/hooks/_lib.sh",
]

# Cases that must NOT be copied: they assume this repo's own content.
EXCLUDED_EVAL_CASES = [
    "evals/cases/chain-rejects-unknown-approver.yaml",
    "evals/cases/plugin-manifest-lists-every-skill.yaml",
    "evals/cases/index-drift-detected.yaml",
    "evals/cases/okf-knowledge-bundle-conforms.yaml",
]


def run_adopt(target, *flags):
    return subprocess.run(
        ["bash", ADOPT_SH, target, *flags],
        capture_output=True,
        text=True,
    )


def snapshot_mtimes(root, rel_paths):
    out = {}
    for rel in rel_paths:
        path = os.path.join(root, rel)
        if os.path.exists(path):
            out[rel] = os.stat(path).st_mtime_ns
    return out


class AdoptScript(unittest.TestCase):
    def test_adopts_expected_files_and_is_executable(self):
        with tempfile.TemporaryDirectory() as root:
            target = os.path.join(root, "target")
            result = run_adopt(target, "--with-hooks")
            self.assertEqual(result.returncode, 0, result.stderr)
            for rel in SAMPLE_FILES:
                self.assertTrue(
                    os.path.exists(os.path.join(target, rel)),
                    "missing after adopt: %s\n%s" % (rel, result.stdout),
                )
            verify_sh = os.path.join(target, "scripts", "verify.sh")
            mode = stat.S_IMODE(os.stat(verify_sh).st_mode)
            self.assertTrue(mode & stat.S_IXUSR, "scripts/verify.sh is not executable")
            for name in ("CLAUDE.md", "GEMINI.md", "AGENTS.md"):
                with open(os.path.join(target, name), encoding="utf-8") as f:
                    self.assertIn("BEGIN GENERATED", f.read(), name)

    def test_eval_cases_filtered_to_hook_gate_deploy(self):
        with tempfile.TemporaryDirectory() as root:
            target = os.path.join(root, "target")
            run_adopt(target, "--with-hooks")
            cases_dir = os.path.join(target, "evals", "cases")
            self.assertTrue(os.path.isdir(cases_dir))
            for name in os.listdir(cases_dir):
                self.assertTrue(
                    name.startswith(("hook-", "gate-", "deploy-")),
                    "unexpected eval case copied: %s" % name,
                )
            for rel in EXCLUDED_EVAL_CASES:
                self.assertFalse(
                    os.path.exists(os.path.join(target, rel)),
                    "case that assumes kit content was copied: %s" % rel,
                )

    def test_second_run_is_noop_and_only_skips(self):
        with tempfile.TemporaryDirectory() as root:
            target = os.path.join(root, "target")
            first = run_adopt(target, "--with-hooks")
            self.assertEqual(first.returncode, 0, first.stderr)
            before = snapshot_mtimes(target, SAMPLE_FILES + HOOK_ONLY_FILES)
            second = run_adopt(target, "--with-hooks")
            self.assertEqual(second.returncode, 0, second.stderr)
            after = snapshot_mtimes(target, SAMPLE_FILES + HOOK_ONLY_FILES)
            self.assertEqual(before, after, "a file was rewritten on a no-op second run")
            self.assertIn("skip (exists)", second.stdout)
            self.assertNotIn("\ncopy: ", "\n" + second.stdout)

    def test_force_overwrites_modified_file(self):
        with tempfile.TemporaryDirectory() as root:
            target = os.path.join(root, "target")
            run_adopt(target, "--with-hooks")
            review = os.path.join(target, "REVIEW.md")
            with open(review, "a", encoding="utf-8") as f:
                f.write("\nlocally modified, should be clobbered by --force\n")
            result = run_adopt(target, "--with-hooks", "--force")
            self.assertEqual(result.returncode, 0, result.stderr)
            with open(review, encoding="utf-8") as f:
                got = f.read()
            with open(os.path.join(KIT, "REVIEW.md"), encoding="utf-8") as f:
                want = f.read()
            self.assertEqual(got, want)

    def test_dry_run_creates_nothing(self):
        with tempfile.TemporaryDirectory() as root:
            target = os.path.join(root, "target")
            result = run_adopt(target, "--with-hooks", "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("copy:", result.stdout)
            self.assertFalse(os.path.exists(target), "--dry-run must not create the target")

    def test_dry_run_on_existing_target_writes_nothing(self):
        with tempfile.TemporaryDirectory() as target:
            result = run_adopt(target, "--with-hooks", "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(os.listdir(target), [], "dry run wrote into an existing target")

    def test_preexisting_claude_md_is_preserved(self):
        with tempfile.TemporaryDirectory() as target:
            marker_text = "# Team notes\n\nDo not remove this paragraph, please.\n"
            with open(os.path.join(target, "CLAUDE.md"), "w", encoding="utf-8") as f:
                f.write(marker_text)
            result = run_adopt(target, "--with-hooks")
            self.assertEqual(result.returncode, 0, result.stderr)
            with open(os.path.join(target, "CLAUDE.md"), encoding="utf-8") as f:
                rendered = f.read()
            self.assertIn("Do not remove this paragraph, please.", rendered)
            self.assertIn("BEGIN GENERATED", rendered)

    def test_with_hooks_installs_hooks_and_settings(self):
        with tempfile.TemporaryDirectory() as root:
            target = os.path.join(root, "target")
            run_adopt(target, "--with-hooks")
            settings = os.path.join(target, ".claude", "settings.json")
            hook = os.path.join(target, ".claude", "hooks", "protect-paths.sh")
            self.assertTrue(os.path.exists(settings))
            self.assertTrue(os.path.exists(hook))
            mode = stat.S_IMODE(os.stat(hook).st_mode)
            self.assertTrue(mode & stat.S_IXUSR, "hook is not executable")

    def test_with_hooks_settings_is_the_kit_template(self):
        # Adopters get the wiring from the template, never from the kit's own .claude/settings.json,
        # which adds the control-plane unlock (knowledge/decisions/self-hooks-on.md).
        with tempfile.TemporaryDirectory() as root:
            target = os.path.join(root, "target")
            result = run_adopt(target, "--with-hooks")
            self.assertEqual(result.returncode, 0, result.stderr)
            with open(os.path.join(target, ".claude", "settings.json"), encoding="utf-8") as f:
                got = f.read()
            template = os.path.join(KIT, "docs", "sdlc", "templates", "claude-settings.json")
            with open(template, encoding="utf-8") as f:
                want = f.read()
            self.assertEqual(got, want)
            for hook in ("protect-paths.sh", "block-secrets.sh", "require-plan.sh",
                         "protect-tests.sh", "production-gate.sh", "stop-verify-reminder.sh"):
                self.assertIn(hook, got, "template does not wire %s" % hook)

    def test_without_with_hooks_hooks_are_absent(self):
        with tempfile.TemporaryDirectory() as root:
            target = os.path.join(root, "target")
            result = run_adopt(target)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(os.path.exists(os.path.join(target, ".claude", "hooks")))
            self.assertFalse(os.path.exists(os.path.join(target, ".claude", "settings.json")))
            self.assertIn("hooks not installed", result.stdout)

    def test_nongit_target_warns_but_exits_zero(self):
        with tempfile.TemporaryDirectory() as target:
            # a plain directory, never `git init`-ed
            result = run_adopt(target, "--with-hooks")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("not a git repository", result.stderr)

    def test_missing_target_is_created_by_default(self):
        with tempfile.TemporaryDirectory() as root:
            target = os.path.join(root, "does", "not", "exist", "yet")
            result = run_adopt(target, "--with-hooks")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(os.path.isdir(target))

    def test_no_create_fails_on_missing_target(self):
        with tempfile.TemporaryDirectory() as root:
            target = os.path.join(root, "does", "not", "exist")
            result = run_adopt(target, "--no-create")
            self.assertEqual(result.returncode, 1)
            self.assertFalse(os.path.exists(target))

    def test_verify_cmds_left_as_placeholder_and_active_set(self):
        with tempfile.TemporaryDirectory() as root:
            target = os.path.join(root, "target")
            run_adopt(target, "--with-hooks")
            with open(os.path.join(target, ".sdlc", "config.env"), encoding="utf-8") as f:
                config = f.read()
            self.assertIn("TODO(adopter): set VERIFY_CMDS", config)
            with open(os.path.join(target, ".sdlc", "active"), encoding="utf-8") as f:
                self.assertEqual(f.read().strip(), "_example")

    def test_preexisting_config_env_left_alone_without_force(self):
        with tempfile.TemporaryDirectory() as target:
            os.makedirs(os.path.join(target, ".sdlc"), exist_ok=True)
            custom = 'VERIFY_CMDS="pytest -q"\nCUSTOM_KEY="1"\n'
            with open(os.path.join(target, ".sdlc", "config.env"), "w", encoding="utf-8") as f:
                f.write(custom)
            result = run_adopt(target, "--with-hooks")
            self.assertEqual(result.returncode, 0, result.stderr)
            with open(os.path.join(target, ".sdlc", "config.env"), encoding="utf-8") as f:
                self.assertEqual(f.read(), custom)

    def test_adopted_target_verify_sh_ends_with_contract_line(self):
        with tempfile.TemporaryDirectory() as target:
            result = run_adopt(target, "--with-hooks")
            self.assertEqual(result.returncode, 0, result.stderr)
            subprocess.run(["git", "init", "-q", target], check=True)
            verify = subprocess.run(
                ["bash", os.path.join(target, "scripts", "verify.sh")],
                cwd=target,
                capture_output=True,
                text=True,
            )
            lines = [l for l in verify.stdout.splitlines() if l.strip()]
            last = lines[-1] if lines else ""
            self.assertRegex(
                last,
                r"^VERIFY: (PASS|FAIL)",
                "scripts/verify.sh in the adopted target did not end with the VERIFY: "
                "contract line -- full output:\n%s\n%s" % (verify.stdout, verify.stderr),
            )


if __name__ == "__main__":
    unittest.main()
