import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
ADOPT_SH = os.path.join(HERE, "adopt.sh")
KIT_ROOT = os.path.dirname(HERE)

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
    ".gemini/settings.json",
    ".gemini/agents/explorer.md",
]

# Cases that must NOT be copied: they assume this repo's own content.
EXCLUDED_EVAL_CASES = [
    "evals/cases/chain-rejects-unknown-approver.yaml",
    "evals/cases/plugin-manifest-lists-every-skill.yaml",
    "evals/cases/index-drift-detected.yaml",
    "evals/cases/okf-knowledge-bundle-conforms.yaml",
]


# NTFS has no POSIX executable bit: Python reports 0o100666 even for a file git records as
# 100755, so `cp -p` cannot preserve what the source does not have. Assert the bit where it
# exists and fall back to "the file is there" on Windows, rather than skipping the whole test.
def assert_executable(case, path, msg):
    case.assertTrue(os.path.isfile(path), msg)
    if os.name != "nt":
        case.assertTrue(os.stat(path).st_mode & stat.S_IXUSR, msg)


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


# --- shared targets ----------------------------------------------------------------------
#
# A full adopt.sh run copies ~200 files and starts python3 twice (context files, indexes).
# That is ~1 s on Linux and ~20 s on the owner's Windows PC, where process creation and the
# per-file antivirus scan dominate; this file used to run it 22 times, one fresh target per
# test, and was more than half of the whole suite's wall clock. Most tests only *read* the
# result of one plain `adopt.sh <missing target> --with-hooks`, so that target is built once
# per class and shared, read-only, by every test that needs exactly that. A test that needs
# its own preconditions (a seeded file, a second run, --force, a git init) gets its own
# scenario. Scenarios are independent directories under one temp root and are built
# concurrently, so the wall clock is the slowest scenario rather than the sum.
#
# Every assertion is unchanged; only who pays for the adopt run moved. A scenario never
# asserts: it records what happened (`first`, `second`, `verify`) and each test asserts on
# that, so a failing adopt still fails the specific tests that care, with adopt's stderr.


class Scenario:
    """One adopt.sh target and the run(s) that produced it; assertions live in the tests."""

    def __init__(self, target):
        self.target = target
        self.existed_before = os.path.exists(target)
        self.first = None
        self.second = None
        self.mtimes_before_second = None
        self.mtimes_after_second = None
        self.verify = None


def _scenario_default(root):
    # A missing, nested target: the one run then also shows that adopt.sh creates the target
    # by default and warns (but continues) when the target is not inside a git repository.
    s = Scenario(os.path.join(root, "default", "does", "not", "exist", "yet"))
    s.first = run_adopt(s.target, "--with-hooks")
    return s


def _scenario_second_run(root):
    s = Scenario(os.path.join(root, "second", "target"))
    s.first = run_adopt(s.target, "--with-hooks")
    s.mtimes_before_second = snapshot_mtimes(s.target, SAMPLE_FILES + HOOK_ONLY_FILES)
    s.second = run_adopt(s.target, "--with-hooks")
    s.mtimes_after_second = snapshot_mtimes(s.target, SAMPLE_FILES + HOOK_ONLY_FILES)
    return s


def _scenario_force(root):
    s = Scenario(os.path.join(root, "force", "target"))
    s.first = run_adopt(s.target, "--with-hooks")
    with open(os.path.join(s.target, "REVIEW.md"), "a", encoding="utf-8") as f:
        f.write("\nlocally modified, should be clobbered by --force\n")
    s.second = run_adopt(s.target, "--with-hooks", "--force")
    return s


def _scenario_no_hooks(root):
    # Nested under the temp root so that on Windows the target is a drive-letter path (`C:\...`),
    # absolute but with no leading slash -- the shape adopt.sh once mistook for a relative path.
    s = Scenario(os.path.join(root, "nohooks", "t"))
    s.first = run_adopt(s.target)
    return s


def _scenario_preexisting_claude_md(root):
    s = Scenario(os.path.join(root, "claudemd"))
    os.makedirs(s.target)
    with open(os.path.join(s.target, "CLAUDE.md"), "w", encoding="utf-8") as f:
        f.write("# Team notes\n\nDo not remove this paragraph, please.\n")
    s.first = run_adopt(s.target, "--with-hooks")
    return s


PREEXISTING_CONFIG_ENV = 'VERIFY_CMDS="pytest -q"\nCUSTOM_KEY="1"\n'


def _scenario_preexisting_config_env(root):
    s = Scenario(os.path.join(root, "configenv"))
    os.makedirs(os.path.join(s.target, ".sdlc"))
    with open(os.path.join(s.target, ".sdlc", "config.env"), "w", encoding="utf-8") as f:
        f.write(PREEXISTING_CONFIG_ENV)
    s.first = run_adopt(s.target, "--with-hooks")
    return s


def _scenario_verify_contract(root):
    s = Scenario(os.path.join(root, "verify"))
    os.makedirs(s.target)
    s.first = run_adopt(s.target, "--with-hooks")
    if s.first.returncode == 0:
        subprocess.run(["git", "init", "-q", s.target], check=True)
        s.verify = subprocess.run(
            ["bash", os.path.join(s.target, "scripts", "verify.sh")],
            cwd=s.target,
            capture_output=True,
            text=True,
        )
    return s


SCENARIOS = {
    "default": _scenario_default,
    "second_run": _scenario_second_run,
    "force": _scenario_force,
    "no_hooks": _scenario_no_hooks,
    "claude_md": _scenario_preexisting_claude_md,
    "config_env": _scenario_preexisting_config_env,
    "verify": _scenario_verify_contract,
}


def _rmtree(path):
    # `git init` in the verify scenario leaves read-only objects that rmtree refuses on Windows.
    def make_writable_and_retry(func, p, exc_info):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except OSError:
            pass

    shutil.rmtree(path, onerror=make_writable_and_retry)


class AdoptScript(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp(prefix="adopt-")
        jobs = int(os.environ.get("SDLC_ADOPT_JOBS") or min(len(SCENARIOS), os.cpu_count() or 2))
        with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
            futures = {name: pool.submit(fn, cls.root) for name, fn in SCENARIOS.items()}
            cls.s = {name: f.result() for name, f in futures.items()}

    @classmethod
    def tearDownClass(cls):
        _rmtree(cls.root)

    def test_adopts_expected_files_and_is_executable(self):
        s = self.s["default"]
        self.assertEqual(s.first.returncode, 0, s.first.stderr)
        for rel in SAMPLE_FILES:
            self.assertTrue(
                os.path.exists(os.path.join(s.target, rel)),
                "missing after adopt: %s\n%s" % (rel, s.first.stdout),
            )
        verify_sh = os.path.join(s.target, "scripts", "verify.sh")
        assert_executable(self, verify_sh, "scripts/verify.sh is not executable")
        for name in ("CLAUDE.md", "GEMINI.md", "AGENTS.md"):
            with open(os.path.join(s.target, name), encoding="utf-8") as f:
                self.assertIn("BEGIN GENERATED", f.read(), name)

    def test_eval_cases_filtered_to_hook_gate_deploy(self):
        s = self.s["default"]
        cases_dir = os.path.join(s.target, "evals", "cases")
        self.assertTrue(os.path.isdir(cases_dir))
        for name in os.listdir(cases_dir):
            self.assertTrue(
                name.startswith(("hook-", "gate-", "deploy-")),
                "unexpected eval case copied: %s" % name,
            )
        for rel in EXCLUDED_EVAL_CASES:
            self.assertFalse(
                os.path.exists(os.path.join(s.target, rel)),
                "case that assumes kit content was copied: %s" % rel,
            )

    def test_second_run_is_noop_and_only_skips(self):
        s = self.s["second_run"]
        self.assertEqual(s.first.returncode, 0, s.first.stderr)
        self.assertEqual(s.second.returncode, 0, s.second.stderr)
        self.assertEqual(
            s.mtimes_before_second, s.mtimes_after_second, "a file was rewritten on a no-op second run"
        )
        self.assertIn("skip (exists)", s.second.stdout)
        self.assertNotIn("\ncopy: ", "\n" + s.second.stdout)

    def test_force_overwrites_modified_file(self):
        s = self.s["force"]
        self.assertEqual(s.second.returncode, 0, s.second.stderr)
        with open(os.path.join(s.target, "REVIEW.md"), encoding="utf-8") as f:
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
        s = self.s["claude_md"]
        self.assertEqual(s.first.returncode, 0, s.first.stderr)
        with open(os.path.join(s.target, "CLAUDE.md"), encoding="utf-8") as f:
            rendered = f.read()
        self.assertIn("Do not remove this paragraph, please.", rendered)
        self.assertIn("BEGIN GENERATED", rendered)

    def test_with_hooks_installs_hooks_and_settings(self):
        s = self.s["default"]
        settings = os.path.join(s.target, ".claude", "settings.json")
        hook = os.path.join(s.target, ".claude", "hooks", "protect-paths.sh")
        self.assertTrue(os.path.exists(settings))
        self.assertTrue(os.path.exists(hook))
        assert_executable(self, hook, "hook is not executable")
        # The Gemini CLI wiring rides along with the hooks (knowledge/decisions/gemini-hooks.md).
        self.assertTrue(os.path.exists(os.path.join(s.target, ".gemini", "settings.json")))
        self.assertTrue(os.path.exists(os.path.join(s.target, ".gemini", "agents", "explorer.md")))

    def test_with_hooks_settings_is_the_kit_template(self):
        # Adopters get the wiring from the template, never from the kit's own .claude/settings.json,
        # which adds the control-plane unlock (knowledge/decisions/self-hooks-on.md).
        s = self.s["default"]
        self.assertEqual(s.first.returncode, 0, s.first.stderr)
        with open(os.path.join(s.target, ".claude", "settings.json"), encoding="utf-8") as f:
            got = f.read()
        template = os.path.join(KIT, "docs", "sdlc", "templates", "claude-settings.json")
        with open(template, encoding="utf-8") as f:
            want = f.read()
        self.assertEqual(got, want)
        for hook in ("protect-paths.sh", "block-secrets.sh", "require-plan.sh",
                     "protect-tests.sh", "production-gate.sh", "stop-verify-reminder.sh"):
            self.assertIn(hook, got, "template does not wire %s" % hook)

    def test_without_with_hooks_hooks_are_absent(self):
        s = self.s["no_hooks"]
        self.assertEqual(s.first.returncode, 0, s.first.stderr)
        self.assertFalse(os.path.exists(os.path.join(s.target, ".claude", "hooks")))
        self.assertFalse(os.path.exists(os.path.join(s.target, ".claude", "settings.json")))
        self.assertIn("hooks not installed", s.first.stdout)

    def test_nongit_target_warns_but_exits_zero(self):
        # The temp root is a plain directory, never `git init`-ed.
        s = self.s["default"]
        self.assertEqual(s.first.returncode, 0, s.first.stderr)
        self.assertIn("not a git repository", s.first.stderr)

    def test_missing_target_is_created_by_default(self):
        s = self.s["default"]
        self.assertFalse(s.existed_before, "scenario must start from a missing target")
        self.assertEqual(s.first.returncode, 0, s.first.stderr)
        self.assertTrue(os.path.isdir(s.target))

    def test_no_create_fails_on_missing_target(self):
        with tempfile.TemporaryDirectory() as root:
            target = os.path.join(root, "does", "not", "exist")
            result = run_adopt(target, "--no-create")
            self.assertEqual(result.returncode, 1)
            self.assertFalse(os.path.exists(target))

    def test_verify_cmds_left_as_placeholder_and_active_set(self):
        s = self.s["default"]
        with open(os.path.join(s.target, ".sdlc", "config.env"), encoding="utf-8") as f:
            config = f.read()
        self.assertIn("TODO(adopter): set VERIFY_CMDS", config)
        with open(os.path.join(s.target, ".sdlc", "active"), encoding="utf-8") as f:
            self.assertEqual(f.read().strip(), "_example")

    def test_preexisting_config_env_left_alone_without_force(self):
        s = self.s["config_env"]
        self.assertEqual(s.first.returncode, 0, s.first.stderr)
        with open(os.path.join(s.target, ".sdlc", "config.env"), encoding="utf-8") as f:
            self.assertEqual(f.read(), PREEXISTING_CONFIG_ENV)

    def test_next_steps_are_literal_text_not_shell_substitutions(self):
        """The Next steps heredoc must not execute anything it merely mentions.

        Its delimiter used to be unquoted, so the backticks around `claude setup-token`
        in step 4 were a command substitution: adopt.sh ran the interactive OAuth flow
        and never returned on any machine with Claude Code installed. CI missed it
        because `claude` is not on PATH there.
        """
        s = self.s["no_hooks"]
        self.assertEqual(s.first.returncode, 0, s.first.stderr)
        self.assertIn("`claude setup-token`", s.first.stdout)

    def test_refuses_a_target_inside_the_kit(self):
        result = run_adopt(os.path.join(KIT_ROOT, "adopt-into-self"))
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("refusing to adopt into the kit itself", result.stderr)
        self.assertFalse(os.path.exists(os.path.join(KIT_ROOT, "adopt-into-self")))

    def test_windows_style_absolute_target_is_not_treated_as_relative(self):
        """A drive-letter path is absolute but does not start with a slash."""
        s = self.s["no_hooks"]
        self.assertEqual(s.first.returncode, 0, s.first.stderr)
        self.assertTrue(os.path.isfile(os.path.join(s.target, ".sdlc", "config.env")))
        stray = [n for n in os.listdir(KIT_ROOT) if n.startswith("C") and os.path.isdir(os.path.join(KIT_ROOT, n))]
        self.assertEqual(stray, [], "adopt.sh wrote a drive-letter directory into the kit")

    def test_adopted_target_verify_sh_ends_with_contract_line(self):
        s = self.s["verify"]
        self.assertEqual(s.first.returncode, 0, s.first.stderr)
        self.assertIsNotNone(s.verify, "verify.sh was not run in the adopted target")
        lines = [l for l in s.verify.stdout.splitlines() if l.strip()]
        last = lines[-1] if lines else ""
        self.assertRegex(
            last,
            r"^VERIFY: (PASS|FAIL)",
            "scripts/verify.sh in the adopted target did not end with the VERIFY: "
            "contract line -- full output:\n%s\n%s" % (s.verify.stdout, s.verify.stderr),
        )


if __name__ == "__main__":
    unittest.main()
