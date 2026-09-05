"""The Gemini CLI side of the kit: .gemini/settings.json wires the same hook scripts Claude
runs, .gemini/agents/ mirrors .claude/agents/ read-only, and the hooks themselves handle what
Gemini (and Claude Code on Windows) hand them: drive-letter paths, and no "ask" decision.

Settings and agents are checked as files; the hook behaviours run the real scripts through
scripts/hooktest.py (see that module for the allow/block contract).
"""
import json
import os
import re
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hooktest import HOOKS_DIR, REAL_ROOT, fake_repo, run_hook  # noqa: E402

SETTINGS = os.path.join(REAL_ROOT, ".gemini", "settings.json")
GEMINI_AGENTS = os.path.join(REAL_ROOT, ".gemini", "agents")
CLAUDE_AGENTS = os.path.join(REAL_ROOT, ".claude", "agents")
HOOK_RE = re.compile(r"\.claude/hooks/([A-Za-z0-9_.-]+\.sh)")
# Gemini CLI built-in tool names (constants in the CLI bundle, v0.58): the ones that read.
READ_ONLY_TOOLS = {
    "read_file", "read_many_files", "glob", "grep_search", "list_directory", "run_shell_command",
}
WRITE_TOOLS = {"write_file", "replace"}


def _front_matter(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path}: no front matter"
    fields, key = {}, None
    for line in m.group(1).splitlines():
        if line.startswith("  - ") and key:
            fields.setdefault(key, []).append(line[4:].strip())
        elif ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            fields[key] = value.strip() or []
    return fields


def _clean_env(**extra):
    env = {k: v for k, v in os.environ.items() if not k.startswith("SDLC_") and k != "RELEASE_APPROVAL"}
    env.update(extra)
    return env


class GeminiSettings(unittest.TestCase):
    def setUp(self):
        with open(SETTINGS, encoding="utf-8") as f:
            self.settings = json.load(f)
        self.hooks = self.settings["hooks"]

    def _entries(self, event):
        return [(e.get("matcher"), h) for e in self.hooks[event] for h in e["hooks"]]

    def test_every_command_points_at_an_existing_executable_hook(self):
        seen = 0
        for event in self.hooks:
            for _matcher, hook in self._entries(event):
                self.assertEqual(hook["type"], "command")
                m = HOOK_RE.search(hook["command"])
                self.assertIsNotNone(m, hook["command"])
                path = os.path.join(HOOKS_DIR, m.group(1))
                self.assertTrue(os.path.isfile(path), path)
                self.assertTrue(os.access(path, os.X_OK), f"{path} is not executable")
                seen += 1
        self.assertGreaterEqual(seen, 6)

    def test_before_tool_covers_gemini_write_and_shell_tools(self):
        for tool in ("write_file", "replace", "run_shell_command"):
            scripts = {
                HOOK_RE.search(h["command"]).group(1)
                for matcher, h in self._entries("BeforeTool")
                if re.fullmatch(matcher, tool)
            }
            for required in ("protect-paths.sh", "block-secrets.sh", "require-plan.sh", "protect-tests.sh", "protect-approvals.sh"):
                self.assertIn(required, scripts, f"{tool} misses {required}")
            if tool == "run_shell_command":
                self.assertIn("production-gate.sh", scripts)

    def test_after_agent_runs_the_verify_reminder(self):
        scripts = {HOOK_RE.search(h["command"]).group(1) for _m, h in self._entries("AfterAgent")}
        self.assertIn("stop-verify-reminder.sh", scripts)

    def test_commands_are_relative_and_run_through_bash(self):
        # Gemini spawns hooks with cwd = the project dir, through `bash -c` on POSIX and
        # `powershell.exe -Command` on Windows. A relative `bash <script>` is the one spelling that
        # works in both; its textual `$GEMINI_PROJECT_DIR` substitution yields a PowerShell
        # single-quoted string that does not concatenate with a following `/path`.
        for event in self.hooks:
            for _m, hook in self._entries(event):
                self.assertTrue(hook["command"].startswith("bash .claude/hooks/"), hook["command"])
                self.assertNotIn("$", hook["command"])


class GeminiAgents(unittest.TestCase):
    def test_mirror_claude_agents_by_name(self):
        claude = {f[:-3] for f in os.listdir(CLAUDE_AGENTS) if f.endswith(".md")}
        gemini = {f[:-3] for f in os.listdir(GEMINI_AGENTS) if f.endswith(".md")}
        self.assertEqual(claude, gemini)
        for name in gemini:
            self.assertEqual(_front_matter(os.path.join(GEMINI_AGENTS, name + ".md"))["name"], name)

    def test_agents_are_read_only(self):
        for f in os.listdir(GEMINI_AGENTS):
            tools = set(_front_matter(os.path.join(GEMINI_AGENTS, f)).get("tools", []))
            self.assertTrue(tools, f)
            self.assertFalse(tools & WRITE_TOOLS, f"{f} may write: {tools & WRITE_TOOLS}")
            self.assertTrue(tools <= READ_ONLY_TOOLS, f"{f}: unknown tools {tools - READ_ONLY_TOOLS}")


def _canon(path, root):
    """Run _lib.sh's canon() on `path` with CLAUDE_PROJECT_DIR=root, the way a hook would."""
    return subprocess.run(
        ["bash", "-c", '. "$1/_lib.sh"; canon "$2"', "_", HOOKS_DIR, path],
        input="{}", capture_output=True, text=True, env=_clean_env(CLAUDE_PROJECT_DIR=root),
    )


class HooksHandleWindowsPaths(unittest.TestCase):
    """Claude Code on Windows and Gemini CLI pass `C:\\repo\\src\\x.ts`; canon() used to treat
    that as relative, so the path landed outside ROOT and every guard allowed it."""

    def test_drive_letter_path_is_repo_relative(self):
        result = _canon("C:\\kit\\src\\a.ts", "C:\\kit")
        self.assertEqual(result.stdout.strip(), "src/a.ts", result.stderr)

    def test_forward_slash_drive_path_is_repo_relative(self):
        result = _canon("C:/kit/.sdlc/config.env", "C:/kit")
        self.assertEqual(result.stdout.strip(), ".sdlc/config.env", result.stderr)

    def test_drive_letter_path_outside_root_stays_absolute(self):
        result = _canon("C:\\other\\src\\a.ts", "C:\\kit")
        self.assertNotEqual(result.stdout.strip(), "src/a.ts", result.stderr)

    def test_require_plan_blocks_drive_letter_write_without_plan(self):
        payload = {"tool_name": "write_file", "tool_input": {"file_path": "C:\\kit\\src\\a.ts", "content": "x"}}
        result = subprocess.run(
            ["bash", os.path.join(HOOKS_DIR, "require-plan.sh")], input=json.dumps(payload),
            capture_output=True, text=True,
            env=_clean_env(CLAUDE_PROJECT_DIR="C:\\kit", SDLC_WORK_ITEM="does-not-exist", PLAN_REQUIRED_PATHS="src"),
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("src/a.ts", result.stderr)


class ProductionGateUnderGemini(unittest.TestCase):
    def _bash(self, command):
        return {"session_id": "s", "hook_event_name": "BeforeTool", "tool_name": "run_shell_command",
                "tool_input": {"command": command}}

    def test_blocks_instead_of_asking(self):
        with fake_repo() as root:
            result = run_hook("production-gate.sh", self._bash("git push origin main"), root,
                              env={"GEMINI_SESSION_ID": "abc"})
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("unattended", result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_still_asks_under_claude(self):
        with fake_repo() as root:
            result = run_hook("production-gate.sh", self._bash("git push origin main"), root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "ask")


class ProtectPathsCoversGemini(unittest.TestCase):
    def test_blocks_gemini_settings(self):
        with fake_repo() as root:
            payload = {"tool_name": "replace", "tool_input": {"file_path": ".gemini/settings.json",
                                                              "old_string": "a", "new_string": "b"}}
            result = run_hook("protect-paths.sh", payload, root)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn(".gemini", result.stderr)


if __name__ == "__main__":
    unittest.main()
