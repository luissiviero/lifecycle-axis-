import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
ADOPT_SH = os.path.join(HERE, "adopt.sh")
KIT_ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import log_ledger  # noqa: E402

PLACEHOLDER = "<your-github-handle>"

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
    "docs/sdlc/github-setup.md",
    "scripts/verify.sh",
    "scripts/check_artifact_chain.py",
    "scripts/gen_context_files.py",
    "scripts/approve.py",
    "scripts/hooktest.py",
    "scripts/github_metrics.py",
    "scripts/bands_config.py",
    "scripts/deploy.sh",
    "scripts/checks/context-drift.sh",
    "evals/README.md",
    "evals/cases/hook-protects-tests-during-fix.yaml",
    "work/_example/intent.md",
    ".github/workflows/sdlc-gate.yml",
    ".github/workflows/agent-evals.yml",
    ".github/workflows/deploy.yml",
    ".github/workflows/bands.yml",
    ".github/CODEOWNERS",
    ".gitignore",
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

HOOK_SCRIPTS = ("protect-paths.sh", "block-secrets.sh", "require-plan.sh",
                "protect-tests.sh", "production-gate.sh", "stop-verify-reminder.sh")


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


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _git(target, *args, env=None):
    return subprocess.run(["git", "-C", target, *args], capture_output=True, text=True, env=env)


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


FORCE_VERIFY_LINE = 'VERIFY_CMDS="pytest -q"'
FORCE_PLAN_LINE = 'PLAN_REQUIRED_PATHS="src"'


def _scenario_force(root):
    s = Scenario(os.path.join(root, "force", "target"))
    s.first = run_adopt(s.target, "--with-hooks")
    with open(os.path.join(s.target, "REVIEW.md"), "a", encoding="utf-8") as f:
        f.write("\nlocally modified, should be clobbered by --force\n")
    # The adopter's own governance values, which --force must carry across the upgrade.
    config_path = os.path.join(s.target, ".sdlc", "config.env")
    lines = []
    for line in _read(config_path).splitlines():
        if line.startswith("VERIFY_CMDS="):
            line = FORCE_VERIFY_LINE
        elif line.startswith("PLAN_REQUIRED_PATHS="):
            line = FORCE_PLAN_LINE
        lines.append(line)
    _write(config_path, "\n".join(lines) + "\n")
    approvers_path = os.path.join(s.target, ".sdlc", "approvers.yaml")
    _write(approvers_path, _read(approvers_path).replace(PLACEHOLDER, "bob"))
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


PREEXISTING_SETTINGS = {
    "permissions": {"allow": ["Bash(npm test)"]},
    "customKey": {"keep": True},
    "hooks": {
        "PreToolUse": [
            {"matcher": "Bash", "hooks": [{"type": "command", "command": "echo mine"}]}
        ]
    },
}


def _scenario_preexisting_settings_json(root):
    # Anyone who has used Claude Code in the repo already has a settings file; the kit's
    # hook wiring must land in it, not be skipped.
    s = Scenario(os.path.join(root, "settings"))
    _write(os.path.join(s.target, ".claude", "settings.json"), json.dumps(PREEXISTING_SETTINGS, indent=2) + "\n")
    s.first = run_adopt(s.target, "--with-hooks")
    s.second = run_adopt(s.target, "--with-hooks")
    return s


BAD_SETTINGS = "{ this is not json\n"


def _scenario_unparseable_settings_json(root):
    s = Scenario(os.path.join(root, "settingsbad"))
    _write(os.path.join(s.target, ".claude", "settings.json"), BAD_SETTINGS)
    s.first = run_adopt(s.target, "--with-hooks")
    return s


def _scenario_differs(root):
    s = Scenario(os.path.join(root, "differs"))
    s.first = run_adopt(s.target)
    with open(os.path.join(s.target, "REVIEW.md"), "a", encoding="utf-8") as f:
        f.write("\nan adopter's own addition\n")
    s.second = run_adopt(s.target)
    return s


def _scenario_approve(root):
    """The adopter's first hour, as the docs describe it: install into a git repo, replace the
    placeholder handle, approve _example with the copied script from a plain shell, commit as
    yourself, and check the install commit against the chain."""
    s = Scenario(os.path.join(root, "approve"))
    os.makedirs(s.target)
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    env.update({
        "GIT_AUTHOR_NAME": "alice", "GIT_AUTHOR_EMAIL": "alice@example.com",
        "GIT_COMMITTER_NAME": "alice", "GIT_COMMITTER_EMAIL": "alice@example.com",
    })
    _git(s.target, "init", "-q", "-b", "main", env=env)
    _git(s.target, "commit", "-q", "--allow-empty", "-m", "base", env=env)
    s.base_sha = _git(s.target, "rev-parse", "HEAD", env=env).stdout.strip()
    s.first = run_adopt(s.target, "--with-hooks")
    if s.first.returncode != 0:
        return s
    approvers_py = os.path.join(s.target, "scripts", "approvers.py")
    s.has_role = subprocess.run(
        [sys.executable, approvers_py, "--has-role", "tech-lead", PLACEHOLDER],
        capture_output=True, text=True, cwd=s.target, env=env,
    )
    for rel in (".sdlc/approvers.yaml", ".github/CODEOWNERS"):
        p = os.path.join(s.target, rel)
        _write(p, _read(p).replace(PLACEHOLDER, "alice"))
    s.approve = subprocess.run(
        [sys.executable, os.path.join(s.target, "scripts", "approve.py"),
         "_example", "intent.md", "spec.md", "plan.md", "--as", "alice"],
        capture_output=True, text=True, cwd=s.target, env=env,
    )
    _git(s.target, "add", "-A", env=env)
    s.commit = _git(s.target, "commit", "-q", "-m", "install the SDLC kit", env=env)
    chain = os.path.join(s.target, "scripts", "check_artifact_chain.py")
    s.chain_full = subprocess.run(
        [sys.executable, chain, "--base", s.base_sha, "--slug", "_example"],
        capture_output=True, text=True, cwd=s.target, env=env,
    )
    s.chain_head = subprocess.run(
        [sys.executable, chain, "--base", "HEAD", "--slug", "_example"],
        capture_output=True, text=True, cwd=s.target, env=env,
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
    "settings_json": _scenario_preexisting_settings_json,
    "settings_bad": _scenario_unparseable_settings_json,
    "differs": _scenario_differs,
    "approve": _scenario_approve,
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


def _copied_paths(stdout):
    return [line[len("copy: "):].strip() for line in stdout.splitlines() if line.startswith("copy: ")]


def _files_section(plan_text):
    out, on = [], False
    for line in plan_text.splitlines():
        if line.startswith("## "):
            on = line.startswith("## Files that change")
            continue
        if on and line.lstrip().startswith("-"):
            out.append(line.lstrip()[1:].strip())
    return out


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

    def test_force_preserves_adopter_values(self):
        """--force is the upgrade path; it must not reset the three values an adopter set by hand."""
        s = self.s["force"]
        self.assertEqual(s.second.returncode, 0, s.second.stderr)
        config = _read(os.path.join(s.target, ".sdlc", "config.env"))
        self.assertIn(FORCE_VERIFY_LINE + "\n", config)
        self.assertIn(FORCE_PLAN_LINE + "\n", config)
        self.assertEqual(config.count("VERIFY_CMDS="), 1)
        self.assertEqual(config.count("PLAN_REQUIRED_PATHS="), 1)
        self.assertNotIn("TODO(adopter)", config)
        approvers = _read(os.path.join(s.target, ".sdlc", "approvers.yaml"))
        self.assertIn("bob", approvers)
        self.assertNotIn(PLACEHOLDER, approvers)
        self.assertNotIn("luissiviero", approvers)
        for key in ("VERIFY_CMDS", "PLAN_REQUIRED_PATHS", "approver handle"):
            self.assertIn("preserved: %s" % key, s.second.stdout)

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

    def test_help_flag(self):
        result = run_adopt("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage: adopt.sh", result.stdout)
        for flag in ("--force", "--dry-run", "--with-hooks", "--no-create", "--help"):
            self.assertIn(flag, result.stdout)
        result = run_adopt("-h")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_preexisting_claude_md_is_preserved(self):
        s = self.s["claude_md"]
        self.assertEqual(s.first.returncode, 0, s.first.stderr)
        with open(os.path.join(s.target, "CLAUDE.md"), encoding="utf-8") as f:
            rendered = f.read()
        self.assertIn("Do not remove this paragraph, please.", rendered)
        self.assertIn("BEGIN GENERATED", rendered)

    def test_fresh_claude_md_has_project_sections(self):
        """The adopter owns the top of CLAUDE.md; the kit's rules are the generated block below it."""
        s = self.s["default"]
        self.assertEqual(s.first.returncode, 0, s.first.stderr)
        text = _read(os.path.join(s.target, "CLAUDE.md"))
        self.assertTrue(text.startswith("# %s\n" % os.path.basename(s.target)), text[:80])
        for heading in ("## Commands", "## Architecture", "## Lessons learned"):
            self.assertIn(heading, text)
            self.assertLess(text.index(heading), text.index("BEGIN GENERATED"), heading)
        self.assertIn("TODO(adopter)", text)
        self.assertNotIn("starter kit", text)
        fragment = _read(os.path.join(s.target, "docs", "sdlc", "rules", "00-chain.md"))
        self.assertIn("This repo follows the AI-native SDLC", fragment)
        self.assertNotIn("starter kit", fragment)
        drift = subprocess.run(
            ["bash", os.path.join(s.target, "scripts", "checks", "context-drift.sh")],
            capture_output=True, text=True, cwd=s.target,
        )
        self.assertEqual(drift.returncode, 0, drift.stdout + drift.stderr)

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
        # which adds the control-plane unlock (knowledge/decisions/self-hooks-on.md). Byte equality
        # holds for a fresh target only; a pre-existing file is merged instead (next test).
        s = self.s["default"]
        self.assertEqual(s.first.returncode, 0, s.first.stderr)
        with open(os.path.join(s.target, ".claude", "settings.json"), encoding="utf-8") as f:
            got = f.read()
        template = os.path.join(KIT, "docs", "sdlc", "templates", "claude-settings.json")
        with open(template, encoding="utf-8") as f:
            want = f.read()
        self.assertEqual(got, want)
        for hook in HOOK_SCRIPTS:
            self.assertIn(hook, got, "template does not wire %s" % hook)

    def test_preexisting_settings_json_is_merged(self):
        s = self.s["settings_json"]
        self.assertEqual(s.first.returncode, 0, s.first.stderr)
        self.assertIn("merged: .claude/settings.json (", s.first.stdout)
        got = json.loads(_read(os.path.join(s.target, ".claude", "settings.json")))
        # The adopter's own content survives untouched.
        self.assertEqual(got["customKey"], {"keep": True})
        self.assertEqual(got["permissions"]["allow"], ["Bash(npm test)"])
        # Missing permission keys are added; existing ones are not replaced.
        self.assertIn("deny", got["permissions"])
        # The kit's hooks are wired, next to the adopter's own hook in the same matcher group.
        bash_groups = [g for g in got["hooks"]["PreToolUse"] if g.get("matcher") == "Bash"]
        self.assertEqual(len(bash_groups), 1, "the Bash matcher group must be reused, not duplicated")
        bash_cmds = [h["command"] for h in bash_groups[0]["hooks"]]
        self.assertIn("echo mine", bash_cmds)
        for hook in HOOK_SCRIPTS:
            if hook != "stop-verify-reminder.sh":
                self.assertTrue(any(hook in c for c in bash_cmds), "Bash group lacks %s" % hook)
        edit_groups = [g for g in got["hooks"]["PreToolUse"] if g.get("matcher") == "Edit|Write|MultiEdit|NotebookEdit"]
        self.assertEqual(len(edit_groups), 1)
        self.assertIn("PostToolUse", got["hooks"])
        self.assertIn("Stop", got["hooks"])
        # Idempotent: the second run has nothing left to add.
        self.assertEqual(s.second.returncode, 0, s.second.stderr)
        self.assertIn("(0 hook entries added)", s.second.stdout)

    def test_unparseable_settings_json_warns_loudly(self):
        s = self.s["settings_bad"]
        self.assertEqual(s.first.returncode, 0, s.first.stderr)
        warning = "WARNING: .claude/settings.json could not be parsed; hooks NOT installed"
        self.assertIn(warning, s.first.stdout)
        self.assertIn(warning, s.first.stderr)
        self.assertEqual(_read(os.path.join(s.target, ".claude", "settings.json")), BAD_SETTINGS)

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

    def test_placeholder_verify_is_red(self):
        """A placeholder that reports VERIFY: PASS is a false green; it must fail until replaced."""
        s = self.s["verify"]
        self.assertEqual(s.first.returncode, 0, s.first.stderr)
        self.assertIsNotNone(s.verify, "verify.sh was not run in the adopted target")
        lines = [l for l in s.verify.stdout.splitlines() if l.strip()]
        self.assertEqual(lines[-1], "VERIFY: FAIL", s.verify.stdout)
        self.assertIn("TODO(adopter): set VERIFY_CMDS", s.verify.stdout)

    def test_plan_required_paths_reset_to_the_adopter_default(self):
        """The kit's own PLAN_REQUIRED_PATHS names the kit's product code (scripts/); an adopter
        gets the application-shaped default instead, whatever the kit's value is at the time."""
        s = self.s["default"]
        with open(os.path.join(s.target, ".sdlc", "config.env"), encoding="utf-8") as f:
            config = f.read()
        self.assertIn('PLAN_REQUIRED_PATHS="src lib app services packages"\n', config)
        self.assertEqual(config.count("PLAN_REQUIRED_PATHS="), 1)
        self.assertIn("set PLAN_REQUIRED_PATHS to the adopter default", s.first.stdout)

    def test_preexisting_config_env_left_alone_without_force(self):
        s = self.s["config_env"]
        self.assertEqual(s.first.returncode, 0, s.first.stderr)
        with open(os.path.join(s.target, ".sdlc", "config.env"), encoding="utf-8") as f:
            self.assertEqual(f.read(), PREEXISTING_CONFIG_ENV)

    def test_handle_rewritten(self):
        """The kit owner's handle never ships as an adopter's approver or code owner."""
        s = self.s["default"]
        self.assertEqual(s.first.returncode, 0, s.first.stderr)
        for rel in (".sdlc/approvers.yaml", ".github/CODEOWNERS"):
            text = _read(os.path.join(s.target, rel))
            self.assertIn(PLACEHOLDER, text, rel)
            self.assertNotIn("luissiviero", text, rel)
        self.assertIn("set the approver handle to %s" % PLACEHOLDER, s.first.stdout)
        a = self.s["approve"]
        self.assertEqual(a.first.returncode, 0, a.first.stderr)
        # The placeholder is nobody, so it holds no role until the adopter replaces it
        # (work/batch-b-followups R-2). approvers.py refuses any `<...>` handle structurally,
        # not through a never-approve entry a global find-and-replace would rewrite.
        self.assertEqual(a.has_role.returncode, 1, a.has_role.stdout + a.has_role.stderr)
        self.assertIn("is a placeholder", a.has_role.stderr + a.has_role.stdout)

    def test_example_is_in_review_with_explicit_file_list(self):
        s = self.s["default"]
        self.assertEqual(s.first.returncode, 0, s.first.stderr)
        example = os.path.join(s.target, "work", "_example")
        for name in ("intent.md", "spec.md", "plan.md"):
            text = _read(os.path.join(example, name))
            self.assertIn("\nstatus: in-review\n", text, name)
            self.assertIn("\napproved-by:\n", text, name)
            self.assertIn("\napproved-on:\n", text, name)
        listed = _files_section(_read(os.path.join(example, "plan.md")))
        self.assertTrue(listed)
        self.assertFalse(any("*" in item for item in listed), listed)
        copied = _copied_paths(s.first.stdout)
        self.assertTrue(copied)
        for rel in copied + [".sdlc/active", "CLAUDE.md", "GEMINI.md", "AGENTS.md", "work/index.md"]:
            self.assertIn(rel, listed, "%s was written but is not in _example's plan" % rel)
        entries, malformed = log_ledger.parse(os.path.join(example, "log.md"))
        self.assertEqual(malformed, [])
        self.assertEqual([(e.artifact, e.to_status, e.actor) for e in entries],
                         [(n, "in-review", "adopt.sh") for n in ("intent.md", "spec.md", "plan.md")])

    def test_delegation_grant_fields_blanked_and_policy_not_shipped(self):
        """work/delegated-mode R-3: adopt.sh blanks delegated-by/delegated-on on the copied
        example the same way it blanks approved-by/approved-on, but does not itself ship
        .sdlc/delegation.yaml -- an adopter turns delegated mode on by copying the template
        by hand (docs/sdlc/github-setup.md), the same way they replace the approver handle."""
        s = self.s["default"]
        self.assertEqual(s.first.returncode, 0, s.first.stderr)
        intent_text = _read(os.path.join(s.target, "work", "_example", "intent.md"))
        self.assertIn("\nmode: supervised\n", intent_text)
        self.assertIn("\ndelegated-by:\n", intent_text)
        self.assertIn("\ndelegated-on:\n", intent_text)
        self.assertFalse(
            os.path.exists(os.path.join(s.target, ".sdlc", "delegation.yaml")),
            "adopt.sh should not ship an enabled delegation policy into a fresh target",
        )
        self.assertTrue(
            os.path.exists(os.path.join(s.target, "docs", "sdlc", "templates", "delegation.yaml")),
            "the template must still be copied so an adopter can turn delegated mode on by hand",
        )

    def test_approve_works_from_a_plain_shell(self):
        s = self.s["approve"]
        self.assertEqual(s.first.returncode, 0, s.first.stderr)
        self.assertEqual(s.approve.returncode, 0, s.approve.stdout + s.approve.stderr)
        for name in ("intent.md", "spec.md", "plan.md"):
            text = _read(os.path.join(s.target, "work", "_example", name))
            self.assertIn("\nstatus: approved\n", text, name)
            self.assertIn("\napproved-by: alice\n", text, name)

    def test_install_commit_chain_passes(self):
        s = self.s["approve"]
        self.assertEqual(s.first.returncode, 0, s.first.stderr)
        self.assertEqual(s.commit.returncode, 0, s.commit.stderr)
        for proc in (s.chain_full, s.chain_head):
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("CHAIN: PASS", proc.stdout)
            self.assertNotIn("not listed", proc.stdout)

    def test_knowledge_indexes_have_no_dangling_links(self):
        s = self.s["default"]
        self.assertEqual(s.first.returncode, 0, s.first.stderr)
        knowledge = os.path.join(s.target, "knowledge")
        indexes = [os.path.join(knowledge, "index.md")] + [
            os.path.join(knowledge, d, "index.md") for d in ("decisions", "lessons", "runbooks", "metrics", "services")
        ]
        for index in indexes:
            self.assertTrue(os.path.isfile(index), index)
            text = _read(index)
            self.assertTrue(text.startswith("---\ntype: index\n"), index)
            for link in re.findall(r"\]\(([^)]+)\)", text):
                if link.startswith(("http://", "https://", "#")):
                    continue
                path = os.path.normpath(os.path.join(os.path.dirname(index), link.split("#")[0]))
                self.assertTrue(os.path.exists(path), "%s links to missing %s" % (index, link))

    def test_differs_from_kit_is_reported(self):
        s = self.s["differs"]
        self.assertEqual(s.second.returncode, 0, s.second.stderr)
        self.assertIn("skip (exists, differs from kit): REVIEW.md", s.second.stdout)
        self.assertNotIn("\ncopy: ", "\n" + s.second.stdout)
        # Files adopt.sh rewrites on purpose are not reported as drift.
        for rel in (".sdlc/config.env", ".sdlc/approvers.yaml", ".github/CODEOWNERS", "work/_example/plan.md"):
            self.assertNotIn("differs from kit): %s" % rel, s.second.stdout)

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
